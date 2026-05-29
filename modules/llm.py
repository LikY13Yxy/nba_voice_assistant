import requests
import json
import os
import logging
import time
import re
from typing import Dict, List, Optional, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from config import config, PLAYER_ALIASES, TEAM_ALIASES, TEAM_NAMES, normalize_player_name, normalize_team_name
except ImportError:
    PLAYER_ALIASES = {}
    TEAM_ALIASES = {}
    TEAM_NAMES = {}
    
    def normalize_player_name(name):
        return name
    
    def normalize_team_name(name):
        return name
    
    class Config:
        LLM_PROVIDER = "deepseek"
        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
        DEEPSEEK_MODEL = "deepseek-chat"
        DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
        MAX_RETRIES = 3
        TIMEOUT = 60
        MAX_HISTORY = 10
        SYSTEM_PROMPT = """你是一个NBA篮球专家助手。请用简洁、易懂的中文回答用户的问题。"""
    
    config = Config()

LLM_PROVIDER = getattr(config, 'LLM_PROVIDER', 'deepseek')
DEEPSEEK_API_KEY = getattr(config, 'DEEPSEEK_API_KEY', os.getenv('DEEPSEEK_API_KEY', ''))
DEEPSEEK_MODEL = getattr(config, 'DEEPSEEK_MODEL', 'deepseek-chat')
DEEPSEEK_URL = getattr(config, 'DEEPSEEK_URL', 'https://api.deepseek.com/chat/completions')
SYSTEM_PROMPT = config.SYSTEM_PROMPT


def check_llm_status() -> bool:
    """检查 LLM 服务状态"""
    if LLM_PROVIDER == "deepseek":
        if not DEEPSEEK_API_KEY:
            logger.error("DeepSeek API Key 未设置")
            return False
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            # 发送一个简单的测试请求
            payload = {
                "model": DEEPSEEK_MODEL,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }
            response = requests.post(DEEPSEEK_URL, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info("DeepSeek API 连接正常")
                return True
            else:
                logger.error(f"DeepSeek API 返回错误: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"DeepSeek API 连接失败: {e}")
            return False
    return False


def chat(prompt: str, system_prompt: str = None) -> str:
    """与 LLM 对话"""
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT
    
    if LLM_PROVIDER == "deepseek":
        return _chat_deepseek(prompt, system_prompt)
    else:
        return "错误：不支持的 LLM 提供商"


def _chat_deepseek(prompt: str, system_prompt: str) -> str:
    """使用 DeepSeek API 进行对话"""
    if not DEEPSEEK_API_KEY:
        return "错误：DeepSeek API Key 未设置。请在 config.py 中设置 DEEPSEEK_API_KEY 或设置环境变量"
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": False
    }
    
    max_retries = getattr(config, 'MAX_RETRIES', 3)
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Sending request to DeepSeek (attempt {attempt + 1}/{max_retries})...")
            response = requests.post(
                DEEPSEEK_URL,
                headers=headers,
                json=payload,
                timeout=getattr(config, 'TIMEOUT', 60)
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                logger.info(f"DeepSeek response received: {content[:50]}...")
                return content
            elif response.status_code == 401:
                return "错误：DeepSeek API Key 无效，请检查配置"
            elif response.status_code == 429:
                logger.warning("请求过于频繁，等待后重试...")
                time.sleep(2 ** attempt)
                continue
            else:
                error_msg = f"DeepSeek API 错误: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', '')}"
                except:
                    pass
                logger.error(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return f"错误：{error_msg}"
                
        except requests.exceptions.Timeout:
            logger.error(f"请求超时 (attempt {attempt + 1})")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return "错误：请求超时，请稍后重试"
        except Exception as e:
            logger.error(f"请求失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(1)
                continue
            return f"错误：{str(e)}"
    
    return "错误：达到最大重试次数"


def chat_stream(prompt: str, system_prompt: str = None):
    """流式对话"""
    if system_prompt is None:
        system_prompt = SYSTEM_PROMPT
    
    if LLM_PROVIDER == "deepseek":
        yield from _chat_deepseek_stream(prompt, system_prompt)
    else:
        yield "错误：不支持的 LLM 提供商"


def _chat_deepseek_stream(prompt: str, system_prompt: str):
    """使用 DeepSeek API 进行流式对话"""
    if not DEEPSEEK_API_KEY:
        yield "错误：DeepSeek API Key 未设置"
        return
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000,
        "stream": True
    }
    
    try:
        response = requests.post(
            DEEPSEEK_URL,
            headers=headers,
            json=payload,
            stream=True,
            timeout=getattr(config, 'TIMEOUT', 60)
        )
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        else:
            yield f"错误：DeepSeek API 返回 {response.status_code}"
    except Exception as e:
        logger.error(f"Stream error: {e}")
        yield f"错误：{str(e)}"


def chat_with_context(prompt: str, context: str = "") -> str:
    """带上下文的对话"""
    if context:
        full_prompt = f"""参考信息：
{context}

用户问题：{prompt}

请根据以上参考信息回答用户问题。如果参考信息不足以回答，请基于你的NBA知识回答。"""
    else:
        full_prompt = prompt
    
    return chat(full_prompt)


def chat_with_context_stream(prompt: str, context: str = ""):
    """带上下文的流式对话"""
    if context:
        full_prompt = f"""参考信息：
{context}

用户问题：{prompt}

请根据以上参考信息回答用户问题。如果参考信息不足以回答，请基于你的NBA知识回答。"""
    else:
        full_prompt = prompt
    
    yield from chat_stream(full_prompt)


def is_data_query(prompt: str) -> bool:
    """判断是否为数据查询"""
    prompt_lower = prompt.lower()
    data_keywords = [
        "今天", "昨天", "明天", "比赛", "比分", "得分", "赢", "输",
        "排名", "战绩", "胜率", "数据", "统计", "得分", "篮板", "助攻",
        "球员", "球队", "赛程", "什么时候", "几点", "对比", "比较",
        "谁更强", "谁更厉害", "历史", "冠军", "MVP", "得分王",
        "篮板王", "助攻王", "排行榜", "top", "第一", "最强", "榜",
        "场均", "命中率", "效率", "mvp", "fmvp"
    ]
    return any(kw in prompt_lower for kw in data_keywords)


def extract_entities(prompt: str) -> Dict:
    """从用户输入中提取实体"""
    prompt_lower = prompt.lower()
    entities = {
        "players": [],
        "teams": [],
        "comparison": False,
        "query_type": None
    }
    
    all_players = list(set(list(PLAYER_ALIASES.values()) + list(PLAYER_ALIASES.keys())))
    all_players = list(set(all_players))
    
    found_players = set()
    for alias, standard_name in PLAYER_ALIASES.items():
        if alias in prompt:
            found_players.add(standard_name)
    
    standard_names = set(PLAYER_ALIASES.values())
    for name in standard_names:
        if name in prompt:
            found_players.add(name)
    
    entities["players"] = list(found_players)
    
    found_teams = set()
    for alias, team_abbr in TEAM_ALIASES.items():
        if alias in prompt:
            found_teams.add(team_abbr)
    
    for abbr in TEAM_NAMES.keys():
        if abbr in prompt.upper():
            found_teams.add(abbr)
    
    entities["teams"] = list(found_teams)
    
    comparison_patterns = [
        r"对比", r"比较", r"谁更强", r"谁更厉害", r"谁更好",
        r"vs", r"VS", r"和.*谁", r"与.*谁"
    ]
    for pattern in comparison_patterns:
        if re.search(pattern, prompt):
            entities["comparison"] = True
            break
    
    if "得分榜" in prompt or "得分王" in prompt or "得分排行" in prompt:
        entities["query_type"] = "top_scorers"
    elif "篮板榜" in prompt or "篮板王" in prompt or "篮板排行" in prompt:
        entities["query_type"] = "top_rebounders"
    elif "助攻榜" in prompt or "助攻王" in prompt or "助攻排行" in prompt:
        entities["query_type"] = "top_assists"
    elif "抢断榜" in prompt or "抢断王" in prompt:
        entities["query_type"] = "top_steals"
    elif "盖帽榜" in prompt or "盖帽王" in prompt:
        entities["query_type"] = "top_blocks"
    elif "冠军" in prompt and ("历史" in prompt or "历年" in prompt):
        entities["query_type"] = "history_champions"
    elif "mvp" in prompt_lower and ("历史" in prompt or "历年" in prompt):
        entities["query_type"] = "history_mvp"
    elif "今天" in prompt and "比赛" in prompt:
        entities["query_type"] = "today_games"
    elif "排名" in prompt or "战绩" in prompt:
        entities["query_type"] = "standings"
    elif "赛程" in prompt:
        entities["query_type"] = "schedule"
    
    return entities


def extract_entities_with_llm(prompt: str) -> Dict:
    """使用 LLM 提取实体"""
    extraction_prompt = f"""你是一个实体识别专家。从用户问题中提取以下信息，返回JSON格式：
- players: 球员名字列表（中文标准名，如"詹姆斯"、"库里"）
- teams: 球队名字列表（中文，如"湖人"、"勇士"）
- query_type: 查询类型，可选值：player_stats, team_schedule, standings, games, comparison, top_scorers, top_rebounders, top_assists, history, other

用户问题：{prompt}

只返回JSON格式，不要其他内容。
示例返回：{{"players": ["詹姆斯"], "teams": ["湖人"], "query_type": "player_stats"}}"""

    try:
        response = chat(extraction_prompt)
        
        response = response.strip()
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            response = json_match.group()
        
        result = json.loads(response)
        
        if "players" not in result:
            result["players"] = []
        if "teams" not in result:
            result["teams"] = []
        if "query_type" not in result:
            result["query_type"] = "other"
        
        normalized_players = []
        for player in result.get("players", []):
            normalized = normalize_player_name(player)
            if normalized not in normalized_players:
                normalized_players.append(normalized)
        result["players"] = normalized_players
        
        normalized_teams = []
        for team in result.get("teams", []):
            normalized = normalize_team_name(team)
            if normalized not in normalized_teams:
                normalized_teams.append(normalized)
        result["teams"] = normalized_teams
        
        result["comparison"] = result.get("query_type") == "comparison" or len(result.get("players", [])) >= 2
        
        return result
        
    except Exception as e:
        logger.warning(f"LLM实体提取失败，使用规则提取: {e}")
        return extract_entities(prompt)


def extract_two_players(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """提取两个球员用于对比"""
    entities = extract_entities(prompt)
    players = entities.get("players", [])
    
    if len(players) >= 2:
        return players[0], players[1]
    elif len(players) == 1:
        return players[0], None
    
    return None, None


def get_intent(prompt: str) -> str:
    """识别用户意图"""
    prompt_lower = prompt.lower()
    
    intents = [
        (r"(今天|今日).*比赛", "today_games"),
        (r"(昨天|昨日).*比赛", "yesterday_games"),
        (r"(明天|明日).*比赛", "tomorrow_games"),
        (r"(排名|战绩)", "standings"),
        (r"(得分榜|得分王|得分排行)", "top_scorers"),
        (r"(篮板榜|篮板王|篮板排行)", "top_rebounders"),
        (r"(助攻榜|助攻王|助攻排行)", "top_assists"),
        (r"(赛程|日程)", "schedule"),
        (r"(对比|比较|谁更强|谁更好)", "comparison"),
        (r"(数据|统计|表现)", "player_stats"),
    ]
    
    for pattern, intent in intents:
        if re.search(pattern, prompt):
            return intent
    
    return "general"


if __name__ == "__main__":
    print("=== LLM 模块测试 ===")
    print(f"LLM 提供商: {LLM_PROVIDER}")
    print(f"检查 API 连接: {check_llm_status()}")
    
    print("\n=== 实体识别测试 ===")
    test_queries = [
        "詹姆斯和库里谁更强？",
        "湖人今天的比赛",
        "NBA得分榜前十",
        "老詹的数据",
        "KD和死神是同一个人吗",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        entities = extract_entities(query)
        print(f"结果: {entities}")
    
    print("\n=== LLM 对话测试 ===")
    result = chat("你好，请简单介绍一下自己")
    print(f"AI: {result}")
