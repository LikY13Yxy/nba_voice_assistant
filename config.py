#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Config:
    # LLM 配置 - 支持多种提供商
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "deepseek")  # 可选: deepseek, openai, ollama
    
    # DeepSeek 配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", " ")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")  # 可选: deepseek-chat, deepseek-reasoner
    DEEPSEEK_URL: str = os.getenv("DEEPSEEK_URL", "https://api.deepseek.com/chat/completions")
    
    # OpenAI 兼容配置（硅基流动等）
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "deepseek-ai/DeepSeek-V3")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    
    # Ollama 配置（备用）
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:latest")
    
    # 通用配置
    MAX_RETRIES: int = 3
    TIMEOUT: int = 60
    MAX_HISTORY: int = 10
    
    SYSTEM_PROMPT: str = """你是NBA篮球专家助手"小篮"。请用专业、热情的中文回答用户的问题。

回答规则：
1. 实时数据查询：结合提供的最新数据回答，数据不足时说明
2. 球员对比：从得分、篮板、助攻、效率等多维度对比，给出明确结论
3. NBA知识：基于你的知识直接回答，不确定时诚实告知
4. 保持友好热情的语气，适当使用emoji

回答控制在200字以内，确保信息准确。"""
    
    # NBA API 配置
    NBA_API_KEY: str = os.getenv("NBA_API_KEY", "")
    NBA_API_HOST: str = "nba-api-free-data.p.rapidapi.com"
    
    # BallDontLie API 配置 (免费)
    BALLDONTLIE_API_KEY: str = os.getenv("BALLDONTLIE_API_KEY", "")
    
    # 备用数据源
    USE_ESPN: bool = True  # ESPN API (免费，无需Key)
    USE_BALLDONTLIE: bool = True  # 免费API
    USE_NBA_API: bool = True  # nba_api库
    USE_THESPORTSDB: bool = True  # TheSportsDB (免费，无需Key)
    
    WAKE_WORD: str = "NBA"
    TTS_VOICE: str = "zh-CN-XiaoxiaoNeural"
    
    WEB_HOST: str = "0.0.0.0"
    WEB_PORT: int = 8080
    
    CACHE_TTL: int = 1800
    
    USE_LIVE_DATA: bool = os.getenv("USE_LIVE_DATA", "true").lower() == "true"


PLAYER_ALIASES: Dict[str, str] = {
    "老詹": "詹姆斯",
    "詹皇": "詹姆斯",
    "King James": "詹姆斯",
    "KD": "杜兰特",
    "书包杜": "杜兰特",
    "死神": "杜兰特",
    "字母哥": "字母哥",
    "Greek Freak": "字母哥",
    "咖喱": "库里",
    "萌神": "库里",
    "Chef Curry": "库里",
    "浓眉": "浓眉",
    "AD": "浓眉",
    "眉子": "浓眉",
    "约老师": "约基奇",
    "小丑": "约基奇",
    "077": "东契奇",
    "卢卡": "东契奇",
    "登哥": "哈登",
    "大胡子": "哈登",
    "威少": "威少",
    "神龟": "威少",
    "卡哇伊": "伦纳德",
    "小卡": "伦纳德",
    "泡椒": "乔治",
    "PG13": "乔治",
    "JB": "巴特勒",
    "吉米": "巴特勒",
    "獭兔": "塔图姆",
    "杰伦": "布朗",
    "大帝": "恩比德",
    "过程": "恩比德",
    "欧文": "欧文",
    "德鲁大叔": "欧文",
    "利指导": "利拉德",
    "表哥": "利拉德",
    "莫兰特": "莫兰特",
    "贾莫兰特": "莫兰特",
    "华子": "爱德华兹",
    "蚁人": "爱德华兹",
    "SGA": "亚历山大",
    "鸭梨": "亚历山大",
    "锡安": "锡安",
    "胖虎": "锡安",
    "布克": "布克",
    "德文布克": "布克",
    "比尔": "比尔",
    "拉文": "拉文",
    "德罗赞": "德罗赞",
    "拉塞尔": "拉塞尔",
    "福克斯": "福克斯",
    "保罗": "保罗",
    "CP3": "保罗",
    "炮哥": "保罗",
}

TEAM_ALIASES: Dict[str, str] = {
    "湖人": "LAL",
    "洛杉矶湖人": "LAL",
    "紫金军团": "LAL",
    "勇士": "GSW",
    "金州勇士": "GSW",
    "湾区勇士": "GSW",
    "凯尔特人": "BOS",
    "绿军": "BOS",
    "绿衫军": "BOS",
    "快船": "LAC",
    "洛杉矶快船": "LAC",
    "船队": "LAC",
    "热火": "MIA",
    "迈阿密热火": "MIA",
    "雄鹿": "MIL",
    "密尔沃基雄鹿": "MIL",
    "掘金": "DEN",
    "丹佛掘金": "DEN",
    "太阳": "PHX",
    "菲尼克斯太阳": "PHX",
    "76人": "PHI",
    "费城76人": "PHI",
    "独行侠": "DAL",
    "达拉斯独行侠": "DAL",
    "小牛": "DAL",
    "灰熊": "MEM",
    "孟菲斯灰熊": "MEM",
    "尼克斯": "NYK",
    "纽约尼克斯": "NYK",
    "国王": "SAC",
    "萨克拉门托国王": "SAC",
    "骑士": "CLE",
    "克利夫兰骑士": "CLE",
    "猛龙": "TOR",
    "多伦多猛龙": "TOR",
    "公牛": "CHI",
    "芝加哥公牛": "CHI",
    "魔术": "ORL",
    "奥兰多魔术": "ORL",
    "步行者": "IND",
    "印第安纳步行者": "IND",
    "奇才": "WAS",
    "华盛顿奇才": "WAS",
    "老鹰": "ATL",
    "亚特兰大老鹰": "ATL",
    "黄蜂": "CHA",
    "夏洛特黄蜂": "CHA",
    "活塞": "DET",
    "底特律活塞": "DET",
    "雷霆": "OKC",
    "俄克拉荷马雷霆": "OKC",
    "火箭": "HOU",
    "休斯顿火箭": "HOU",
    "鹈鹕": "NOP",
    "新奥尔良鹈鹕": "NOP",
    "爵士": "UTA",
    "犹他爵士": "UTA",
    "马刺": "SAS",
    "圣安东尼奥马刺": "SAS",
    "森林狼": "MIN",
    "明尼苏达森林狼": "MIN",
    "开拓者": "POR",
    "波特兰开拓者": "POR",
}

TEAM_NAMES: Dict[str, str] = {
    "LAL": "洛杉矶湖人",
    "GSW": "金州勇士",
    "BOS": "波士顿凯尔特人",
    "LAC": "洛杉矶快船",
    "MIA": "迈阿密热火",
    "MIL": "密尔沃基雄鹿",
    "DEN": "丹佛掘金",
    "PHX": "菲尼克斯太阳",
    "PHI": "费城76人",
    "DAL": "达拉斯独行侠",
    "MEM": "孟菲斯灰熊",
    "NYK": "纽约尼克斯",
    "SAC": "萨克拉门托国王",
    "CLE": "克利夫兰骑士",
    "TOR": "多伦多猛龙",
    "CHI": "芝加哥公牛",
    "ORL": "奥兰多魔术",
    "IND": "印第安纳步行者",
    "WAS": "华盛顿奇才",
    "ATL": "亚特兰大老鹰",
    "CHA": "夏洛特黄蜂",
    "DET": "底特律活塞",
    "OKC": "俄克拉荷马雷霆",
    "HOU": "休斯顿火箭",
    "NOP": "新奥尔良鹈鹕",
    "UTA": "犹他爵士",
    "SAS": "圣安东尼奥马刺",
    "MIN": "明尼苏达森林狼",
    "POR": "波特兰开拓者",
}


def normalize_player_name(name: str) -> str:
    return PLAYER_ALIASES.get(name, name)


def normalize_team_name(name: str) -> str:
    if name.upper() in TEAM_NAMES:
        return name.upper()
    return TEAM_ALIASES.get(name, name)


config = Config()
