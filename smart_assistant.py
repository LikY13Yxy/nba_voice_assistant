#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from modules.llm import (
    chat,
    chat_with_context,
    chat_with_context_stream,
    is_data_query,
    extract_entities,
    extract_entities_with_llm,
    get_intent,
    check_llm_status
)
from modules.nba_live_data import (
    get_player_info,
    get_standings,
    get_today_games,
    get_team_schedule,
    get_league_leaders,
    compare_players
)
from modules.voice import speech_to_text, text_to_speech

# 导入RAG知识库
try:
    from modules.knowledge_base import get_knowledge_context
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("知识库模块未加载")

CONVERSATION_HISTORY = []


def add_to_history(role: str, content: str):
    CONVERSATION_HISTORY.append({"role": role, "content": content})
    if len(CONVERSATION_HISTORY) > config.MAX_HISTORY:
        CONVERSATION_HISTORY.pop(0)


def build_context_from_history() -> str:
    if not CONVERSATION_HISTORY:
        return ""
    return "\n".join([f"{msg['role']}: {msg['content']}" for msg in CONVERSATION_HISTORY])


def understand_and_answer(user_input: str, use_api: bool = True) -> str:
    print(f"\n👤 用户: {user_input}")
    add_to_history("user", user_input)
    
    context = ""
    
    if use_api and is_data_query(user_input):
        entities = extract_entities(user_input)
        query_type = entities.get("query_type")
        intent = get_intent(user_input)
        
        if entities["players"]:
            for player in entities["players"]:
                print(f"🔍 检测到球员查询: {player}")
                player_info = get_player_info(player)
                context += f"\n{player_info}\n"
        
        if entities["teams"]:
            for team in entities["teams"]:
                print(f"🔍 检测到球队查询: {team}")
                team_info = get_team_schedule(team)
                context += f"\n{team_info}\n"
        
        if query_type == "today_games" or intent == "today_games":
            print("🔍 查询今日比赛")
            games = get_today_games()
            context += f"\n{games}\n"
        
        if query_type == "standings" or intent == "standings":
            print("🔍 查询排名")
            standings = get_standings()
            context += f"\n{standings}\n"
        
        if query_type == "top_scorers":
            print("🔍 查询得分榜")
            leaders = get_league_leaders("PTS", 10)
            context += f"\n{leaders}\n"
        
        if query_type == "top_rebounders":
            print("🔍 查询篮板榜")
            leaders = get_league_leaders("REB", 10)
            context += f"\n{leaders}\n"
        
        if query_type == "top_assists":
            print("🔍 查询助攻榜")
            leaders = get_league_leaders("AST", 10)
            context += f"\n{leaders}\n"
        
        if entities["comparison"] and len(entities["players"]) >= 2:
            print(f"🔍 球员对比: {entities['players']}")
            comparison = compare_players(entities["players"][0], entities["players"][1])
            context += f"\n{comparison}\n"
        
        # 添加RAG知识库上下文
        if RAG_AVAILABLE:
            print("📚 检索知识库...")
            knowledge_context = get_knowledge_context(user_input)
            if knowledge_context:
                context += f"\n{knowledge_context}\n"

        if context:
            print("📡 整合数据生成回答...")
            history_context = build_context_from_history()
            full_context = f"历史对话:\n{history_context}\n\n参考信息:\n{context}" if history_context else f"参考信息:\n{context}"
            answer = chat_with_context(user_input, full_context)
        else:
            answer = chat(user_input)
    else:
        print("💭 使用纯LLM回答...")
        # 即使是纯LLM模式，也可以添加知识库上下文
        context_parts = []

        history_context = build_context_from_history()
        if history_context:
            context_parts.append(f"历史对话:\n{history_context}")

        if RAG_AVAILABLE:
            knowledge_context = get_knowledge_context(user_input)
            if knowledge_context:
                context_parts.append(knowledge_context)
                print("📚 已添加知识库参考")

        if context_parts:
            full_context = "\n\n".join(context_parts)
            answer = chat_with_context(user_input, full_context)
        else:
            answer = chat(user_input)
    
    add_to_history("assistant", answer)
    print(f"\n🤖 AI: {answer}")
    return answer


def voice_mode():
    print("\n🎤 进入语音模式，说出你的问题")
    print("📝 也可以输入文字")
    print("🔙 输入 'back' 返回主菜单")
    print("-" * 40)
    
    while True:
        try:
            print("\n🎤 请说话... (或输入文字)")
            user_input = speech_to_text()
            
            if not user_input:
                print("❌ 未检测到语音，请再说一次或输入文字")
                user_input = input("📝 请输入: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["back", "返回", "退出"]:
                print("🔙 返回主菜单")
                break
            
            answer = understand_and_answer(user_input)
            text_to_speech(answer)
            
        except KeyboardInterrupt:
            print("\n\n🔙 返回主菜单")
            break
        except Exception as e:
            print(f"\n❌ 语音模式错误: {e}")


def text_mode():
    print("\n📝 进入文字模式")
    print("🔙 输入 'back' 返回主菜单")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\n👤 你想说: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["back", "返回"]:
                print("🔙 返回主菜单")
                break
            
            if user_input.lower() in ["quit", "q", "退出"]:
                print("👋 再见！")
                sys.exit(0)
            
            answer = understand_and_answer(user_input)
            print(f"🤖 AI: {answer}")
            
        except KeyboardInterrupt:
            print("\n\n🔙 返回主菜单")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


def show_menu():
    print("\n" + "=" * 50)
    print("🏀 NBA智能语音助手 v2.1")
    print("=" * 50)
    print("1. 语音模式 🎤")
    print("2. 文字模式 📝")
    print("3. 退出 quit")
    print("=" * 50)


def main():
    print("=" * 50)
    print("🏀 NBA智能语音助手 v2.1")
    print(f"   LLM提供商: {config.LLM_PROVIDER}")
    print(f"   实时数据: {'开启' if config.USE_LIVE_DATA else '关闭'}")
    print("=" * 50)

    # 检查 LLM 状态
    print("\n🔍 正在检查 LLM 服务...")
    if check_llm_status():
        print("✅ LLM 服务正常")
    else:
        print("⚠️ LLM 服务异常，请检查 API Key 配置")
        print(f"   当前提供商: {config.LLM_PROVIDER}")
        if config.LLM_PROVIDER == "deepseek":
            print("   请设置 DEEPSEEK_API_KEY 环境变量或在 config.py 中配置")

    print("\n1. 语音模式 🎤")
    print("2. 文字模式 📝")
    print("3. 退出 quit")
    print("=" * 50)
    
    while True:
        try:
            choice = input("\n👉 请选择模式 (1/2/3): ").strip()
            
            if choice == "1":
                voice_mode()
                show_menu()
            elif choice == "2":
                text_mode()
                show_menu()
            elif choice in ["3", "quit", "q"]:
                print("👋 再见！")
                break
            else:
                print("❌ 无效选择，请输入 1、2 或 3")
                
        except KeyboardInterrupt:
            print("\n\n👋 再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


if __name__ == "__main__":
    main()
