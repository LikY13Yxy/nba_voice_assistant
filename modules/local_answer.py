#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sqlite3
import os
import logging
from typing import Optional, Dict, List

from modules.local_database import (
    init_database, query_player, query_player_stats,
    query_player_season_stats, query_team, query_champions,
    query_records, query_mvp, query_faq, compare_two_players
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'nba_local.db')

_db_initialized = False


def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        init_database()
        _db_initialized = True


def _normalize_player_name(name: str) -> Optional[str]:
    _ensure_db()
    player = query_player(name)
    if player:
        return player['name_cn']
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name_cn, aliases FROM players")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        r = dict(row)
        if r['aliases']:
            aliases = [a.strip() for a in r['aliases'].split(',')]
            if name in aliases or name in r['name_cn']:
                return r['name_cn']
    return None


def _normalize_team_name(name: str) -> Optional[str]:
    _ensure_db()
    team = query_team(name)
    if team:
        return team['abbr']
    return None


def can_answer_locally(user_input: str) -> bool:
    _ensure_db()
    result = local_answer(user_input)
    return result is not None


def local_answer(user_input: str) -> Optional[str]:
    _ensure_db()
    q = user_input.strip()

    answer = _try_live_games(q)
    if answer:
        return answer

    answer = _try_live_standings(q)
    if answer:
        return answer

    answer = _try_nba_news(q)
    if answer:
        return answer

    answer = _try_comparison(q)
    if answer:
        return answer

    answer = _try_player_query(q)
    if answer:
        return answer

    answer = _try_team_query(q)
    if answer:
        return answer

    answer = _try_champion_query(q)
    if answer:
        return answer

    answer = _try_mvp_query(q)
    if answer:
        return answer

    answer = _try_record_query(q)
    if answer:
        return answer

    answer = _try_faq(q)
    if answer:
        return answer

    return None


def _try_live_games(q: str) -> Optional[str]:
    game_keywords = ["比赛", "赛程", "对战", "vs", "对决"]
    time_keywords = ["今日", "今天", "最近", "近期", "明天", "后天", "本周"]
    
    has_game_kw = any(kw in q for kw in game_keywords)
    has_time_kw = any(kw in q for kw in time_keywords)
    
    if has_game_kw and has_time_kw:
        try:
            from modules.nba_live_data import get_today_games
            result = get_today_games()
            if result and "暂无" not in result and "失败" not in result:
                return result
        except Exception as e:
            logger.warning(f"获取今日比赛失败: {e}")
        
        try:
            from modules.nba_data import get_today_games as get_local_games
            return get_local_games()
        except Exception as e:
            logger.warning(f"获取本地比赛数据失败: {e}")
            return None
    return None


def _try_live_standings(q: str) -> Optional[str]:
    if any(kw in q for kw in ["排名", "排行", "积分榜", "战绩"]):
        try:
            from modules.nba_live_data import get_standings
            result = get_standings()
            if result and "失败" not in result:
                return result
        except Exception as e:
            logger.warning(f"获取排名失败: {e}")
        
        try:
            from modules.nba_data import get_standings as get_local_standings
            return get_local_standings()
        except Exception as e:
            logger.warning(f"获取本地排名数据失败: {e}")
            return None
    return None


def _try_nba_news(q: str) -> Optional[str]:
    if any(kw in q for kw in ["新闻", "资讯", "最新消息", "最新新闻", "NBA新闻", "头条"]):
        try:
            from modules.data_provider import data_provider
            articles = data_provider.get_espn_news(limit=5)
            if articles:
                result = "📰 NBA最新新闻\n"
                result += "=" * 40 + "\n"
                for i, a in enumerate(articles[:5], 1):
                    headline = a.get('headline', 'N/A')
                    description = a.get('description', '')
                    result += f"{i}. {headline}\n"
                    if description:
                        result += f"   {description[:100]}\n"
                    result += "\n"
                return result
        except Exception as e:
            logger.warning(f"获取NBA新闻失败: {e}")
            return None
    return None


def _try_player_query(q: str) -> Optional[str]:
    player_keywords = ["身高", "体重", "位置", "球衣", "号码", "选秀", "国籍", "出生", "生日",
                       "哪个队", "效力", "数据", "得分", "篮板", "助攻", "抢断", "盖帽",
                       "命中率", "三分", "罚球", "场均", "生涯", "赛季", "介绍", "是谁",
                       "什么位置", "多高", "多重", "哪年选秀"]

    is_player_query = any(kw in q for kw in player_keywords)

    if not is_player_query:
        name_match = _extract_player_name(q)
        if name_match and len(q) <= 15:
            is_player_query = True

    if not is_player_query:
        return None

    name = _extract_player_name(q)
    if not name:
        return None

    player = query_player(name)
    if not player:
        return None

    if any(kw in q for kw in ["数据", "得分", "篮板", "助攻", "抢断", "盖帽", "命中率", "三分", "罚球", "场均", "生涯", "赛季"]):
        stats = query_player_stats(name)
        season = query_player_season_stats(name)
        if stats:
            result = f"📊 {player['name_cn']}（{player['name_en']}）生涯数据：\n"
            result += f"  赛季数：{stats['seasons']}赛季 | 出场：{stats['games_played']}场\n"
            result += f"  场均：{stats['ppg']}分 {stats['rpg']}板 {stats['apg']}助 {stats['spg']}断 {stats['bpg']}帽\n"
            result += f"  命中率：投篮{stats['fg_pct']}% | 三分{stats['three_pct']}% | 罚球{stats['ft_pct']}%\n"
            result += f"  生涯总计：{stats['total_points']}分 {stats['total_rebounds']}板 {stats['total_assists']}助"
            if season:
                latest = season[0]
                result += f"\n\n📈 {latest['season']}赛季：{latest['ppg']}分 {latest['rpg']}板 {latest['apg']}助 | 投篮{latest['fg_pct']}% | 三分{latest['three_pct']}%"
            return result

    if any(kw in q for kw in ["身高", "多高"]):
        return f"🏀 {player['name_cn']}的身高是 {player['height_cm']}cm（约{player['height_cm']/100:.2f}米）"

    if any(kw in q for kw in ["体重", "多重"]):
        return f"🏀 {player['name_cn']}的体重是 {player['weight_kg']}kg"

    if any(kw in q for kw in ["位置", "什么位置"]):
        return f"🏀 {player['name_cn']}的位置是 {player['position']}"

    if any(kw in q for kw in ["球衣", "号码"]):
        return f"🏀 {player['name_cn']}的球衣号码是 {player['jersey_number']}号"

    if any(kw in q for kw in ["选秀", "哪年"]):
        draft_info = f"{player['draft_year']}年第{player['draft_round']}轮第{player['draft_number']}顺位"
        return f"🏀 {player['name_cn']}于{draft_info}被选中"

    if any(kw in q for kw in ["国籍", "国家"]):
        return f"🏀 {player['name_cn']}的国籍是 {player['country']}"

    if any(kw in q for kw in ["出生", "生日"]):
        return f"🏀 {player['name_cn']}的出生日期是 {player['birth_date']}"

    if any(kw in q for kw in ["哪个队", "效力"]):
        team = query_team(player['team_abbr'])
        team_name = team['name_cn'] if team else player['team_abbr']
        return f"🏀 {player['name_cn']}目前效力于 {team_name}"

    if player['description']:
        result = f"🏀 {player['name_cn']}（{player['name_en']}）\n"
        result += f"  位置：{player['position']} | 球衣：{player['jersey_number']}号\n"
        result += f"  身高：{player['height_cm']}cm | 体重：{player['weight_kg']}kg\n"
        team = query_team(player['team_abbr'])
        team_name = team['name_cn'] if team else player['team_abbr']
        result += f"  球队：{team_name} | 选秀：{player['draft_year']}年\n"
        result += f"\n{player['description']}"
        return result

    return None


def _try_team_query(q: str) -> Optional[str]:
    team_keywords = ["冠军", "几次", "成立", "哪年成立", "城市", "分区", "联盟", "球队介绍",
                     "总冠军", "夺冠", "几个冠军"]

    is_team_query = any(kw in q for kw in team_keywords)
    if not is_team_query:
        return None

    team_abbr = _extract_team_name(q)
    if not team_abbr:
        return None

    team = query_team(team_abbr)
    if not team:
        return None

    if any(kw in q for kw in ["冠军", "几次", "总冠军", "夺冠", "几个冠军"]):
        return f"🏆 {team['name_cn']}历史上共获得 {team['championships']} 次NBA总冠军"

    if any(kw in q for kw in ["成立", "哪年"]):
        return f"🏀 {team['name_cn']}成立于 {team['founded_year']} 年"

    if any(kw in q for kw in ["城市"]):
        return f"🏀 {team['name_cn']}位于 {team['city']}"

    if any(kw in q for kw in ["分区", "联盟"]):
        return f"🏀 {team['name_cn']}属于 {team['conference']}联盟 {team['division']}赛区"

    result = f"🏀 {team['name_cn']}（{team['name_en']}）\n"
    result += f"  城市：{team['city']} | 联盟：{team['conference']} | 分区：{team['division']}\n"
    result += f"  成立：{team['founded_year']}年 | 总冠军：{team['championships']}次\n"
    if team['description']:
        result += f"\n{team['description']}"
    return result


def _try_champion_query(q: str) -> Optional[str]:
    if not any(kw in q for kw in ["冠军", "总冠军", "夺冠", "谁赢了", "哪年"]):
        return None

    year_match = re.search(r'(20\d{2}|19\d{2})', q)
    if year_match:
        year = int(year_match.group(1))
        champions = query_champions(year)
        if champions:
            c = champions[0]
            result = f"🏆 {c['year']}年NBA总冠军：{c['champion']}\n"
            result += f"  亚军：{c['runner_up']}\n"
            result += f"  比分：{c['score']}\n"
            result += f"  常规赛MVP：{c['mvp']}\n"
            result += f"  总决赛MVP：{c['finals_mvp']}"
            return result
        return f"未找到{year}年的冠军数据"

    if any(kw in q for kw in ["本赛季", "今年", "当前", "最新"]):
        champions = query_champions()
        if champions:
            c = champions[0]
            result = f"🏆 {c['year']}年NBA总冠军：{c['champion']}\n"
            result += f"  亚军：{c['runner_up']}\n"
            result += f"  比分：{c['score']}\n"
            result += f"  常规赛MVP：{c['mvp']}\n"
            result += f"  总决赛MVP：{c['finals_mvp']}"
            return result

    if any(kw in q for kw in ["历年", "历史", "最近", "近几", "列表"]):
        champions = query_champions()
        if champions:
            result = "🏆 近年NBA总冠军：\n"
            for c in champions[:10]:
                result += f"  {c['year']}年：{c['champion']}（{c['score']}）FMVP: {c['finals_mvp']}\n"
            return result

    return None


def _try_mvp_query(q: str) -> Optional[str]:
    if not any(kw in q for kw in ["MVP", "mvp", "最有价值"]):
        return None

    year_match = re.search(r'(20\d{2}|19\d{2})', q)
    if year_match:
        year = int(year_match.group(1))
        mvps = query_mvp(year=year)
        if mvps:
            m = mvps[0]
            return f"🏅 {m['year']}年{m['award_type']}：{m['player']}（{m['team']}）"
        return f"未找到{year}年的MVP数据"

    player_name = _extract_player_name(q)
    if player_name:
        mvps = query_mvp(player=player_name)
        if mvps:
            result = f"🏅 {player_name}获得的MVP：\n"
            for m in mvps:
                result += f"  {m['year']}年 {m['award_type']}（{m['team']}）\n"
            return result

    if any(kw in q for kw in ["本赛季", "今年", "当前", "最新"]):
        mvps = query_mvp()
        if mvps:
            m = mvps[0]
            return f"🏅 {m['year']}年{m['award_type']}：{m['player']}（{m['team']}）"

    if any(kw in q for kw in ["历年", "历史", "最近", "列表"]):
        mvps = query_mvp()
        if mvps:
            result = "🏅 近年NBA常规赛MVP：\n"
            for m in mvps[:10]:
                result += f"  {m['year']}年：{m['player']}（{m['team']}）\n"
            return result

    return None


def _try_record_query(q: str) -> Optional[str]:
    record_keywords = {
        "得分王": "得分", "得分纪录": "得分", "最高分": "得分", "得分最多": "得分",
        "篮板王": "篮板", "篮板纪录": "篮板", "最多篮板": "篮板",
        "助攻王": "助攻", "助攻纪录": "助攻", "最多助攻": "助攻",
        "抢断王": "抢断", "盖帽王": "盖帽",
        "三双": "三双", "连胜": "连胜",
        "纪录": None, "记录": None, "历史之最": None, "历史最高": None,
    }

    category = None
    for kw, cat in record_keywords.items():
        if kw in q:
            category = cat
            break

    if category is None and not any(kw in q for kw in ["纪录", "记录", "历史之最", "历史最高", "之最"]):
        return None

    records = query_records(category)
    if not records:
        return None

    is_who_question = any(kw in q for kw in ["是谁", "谁是", "谁", "哪个", "哪个人"])
    is_asking_king = any(kw in q for kw in ["得分王", "篮板王", "助攻王", "抢断王", "盖帽王", "三分王"])

    if is_asking_king and category and records:
        first = records[0]
        return f"🏆 NBA历史{category}王是{first['holder']}，{first['value']}"

    if category:
        result = f"📊 NBA{category}纪录：\n"
    else:
        result = "📊 NBA历史纪录：\n"

    for r in records[:8]:
        result += f"  {r['record_type']}：{r['holder']} - {r['value']}\n"
        if r['description']:
            result += f"    💡 {r['description']}\n"
    return result


def _try_comparison(q: str) -> Optional[str]:
    comparison_patterns = [r"对比", r"比较", r"谁更强", r"谁更厉害", r"谁更好", r"vs", r"VS", r"和.*谁", r"与.*谁"]
    is_comparison = any(re.search(p, q) for p in comparison_patterns)
    if not is_comparison:
        return None

    names = _extract_two_player_names(q)
    if not names:
        return None

    name1, name2 = names
    cmp = compare_two_players(name1, name2)
    if not cmp:
        return None

    p1, p2 = cmp['player1'], cmp['player2']
    pn1, pn2 = p1['player']['name_cn'], p2['player']['name_cn']

    result = f"⚔️ {pn1} vs {pn2} 生涯数据对比：\n\n"
    result += f"{'项目':<8} {pn1:<10} {pn2:<10}\n"
    result += f"{'─' * 30}\n"
    result += f"{'身高':<8} {p1['player']['height_cm']}cm{'':<5} {p2['player']['height_cm']}cm\n"
    result += f"{'体重':<8} {p1['player']['weight_kg']}kg{'':<5} {p2['player']['weight_kg']}kg\n"
    result += f"{'位置':<8} {p1['player']['position']:<10} {p2['player']['position']}\n"
    result += f"{'赛季':<8} {p1['seasons']:<10} {p2['seasons']}\n"
    result += f"{'─' * 30}\n"
    result += f"{'场均得分':<8} {p1['ppg']:<10} {p2['ppg']}\n"
    result += f"{'场均篮板':<8} {p1['rpg']:<10} {p2['rpg']}\n"
    result += f"{'场均助攻':<8} {p1['apg']:<10} {p2['apg']}\n"
    result += f"{'场均抢断':<8} {p1['spg']:<10} {p2['spg']}\n"
    result += f"{'场均盖帽':<8} {p1['bpg']:<10} {p2['bpg']}\n"
    result += f"{'─' * 30}\n"
    result += f"{'投篮%':<8} {p1['fg_pct']}%{'':<7} {p2['fg_pct']}%\n"
    result += f"{'三分%':<8} {p1['three_pct']}%{'':<7} {p2['three_pct']}%\n"
    result += f"{'罚球%':<8} {p1['ft_pct']}%{'':<7} {p2['ft_pct']}%\n"

    ppg_winner = pn1 if p1['ppg'] > p2['ppg'] else pn2
    rpg_winner = pn1 if p1['rpg'] > p2['rpg'] else pn2
    apg_winner = pn1 if p1['apg'] > p2['apg'] else pn2

    result += f"\n💡 简评：{ppg_winner}得分更强，{rpg_winner}篮板更强，{apg_winner}助攻更强"
    return result


def _try_faq(q: str) -> Optional[str]:
    return query_faq(q)


def _extract_player_name(q: str) -> Optional[str]:
    from config import PLAYER_ALIASES
    for alias, standard in PLAYER_ALIASES.items():
        if alias in q:
            return standard
    all_standards = set(PLAYER_ALIASES.values())
    for standard in all_standards:
        if standard in q:
            return standard
    name = _normalize_player_name(q)
    if name:
        return name
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name_cn, aliases FROM players")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        r = dict(row)
        if r['name_cn'] in q:
            return r['name_cn']
        if r['aliases']:
            aliases = [a.strip() for a in r['aliases'].split(',')]
            for alias in aliases:
                if alias in q:
                    return r['name_cn']
    return None


def _extract_team_name(q: str) -> Optional[str]:
    from config import TEAM_ALIASES
    for alias, abbr in TEAM_ALIASES.items():
        if alias in q:
            return abbr
    abbr = _normalize_team_name(q)
    if abbr:
        return abbr
    return None


def _extract_two_player_names(q: str) -> Optional[tuple]:
    from config import PLAYER_ALIASES
    found = []
    for alias, standard in PLAYER_ALIASES.items():
        if alias in q and standard not in found:
            found.append(standard)
    if len(found) < 2:
        all_standards = set(PLAYER_ALIASES.values())
        for standard in all_standards:
            if standard in q and standard not in found:
                found.append(standard)
    if len(found) < 2:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT name_cn, aliases FROM players")
        rows = c.fetchall()
        conn.close()
        for row in rows:
            r = dict(row)
            matched = False
            if r['name_cn'] in q and r['name_cn'] not in found:
                found.append(r['name_cn'])
                matched = True
            if not matched and r['aliases']:
                aliases = [a.strip() for a in r['aliases'].split(',')]
                for alias in aliases:
                    if alias in q and r['name_cn'] not in found:
                        found.append(r['name_cn'])
                        break
    if len(found) >= 2:
        return found[0], found[1]
    return None


if __name__ == "__main__":
    print("=== 本地智能回答测试 ===\n")

    test_queries = [
        "詹姆斯身高多少",
        "库里生涯数据",
        "湖人几个冠军",
        "2024年NBA冠军是谁",
        "NBA历史得分王是谁",
        "詹姆斯和库里谁更强",
        "NBA有几支球队",
        "约基奇是什么位置",
        "最近MVP是谁",
        "什么是三双",
        "杜兰特选秀顺位",
        "字母哥体重",
    ]

    for query in test_queries:
        print(f"\n❓ {query}")
        answer = local_answer(query)
        if answer:
            print(f"✅ {answer}")
        else:
            print("❌ 无法本地回答")
