import requests
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEAM_INFO = {
    "LAL": {"name": "洛杉矶湖人", "city": "洛杉矶", "conference": "西部", "division": "太平洋"},
    "GSW": {"name": "金州勇士", "city": "金州", "conference": "西部", "division": "太平洋"},
    "BOS": {"name": "波士顿凯尔特人", "city": "波士顿", "conference": "东部", "division": "大西洋"},
    "LAC": {"name": "洛杉矶快船", "city": "洛杉矶", "conference": "西部", "division": "太平洋"},
    "MIA": {"name": "迈阿密热火", "city": "迈阿密", "conference": "东部", "division": "东南"},
    "MIL": {"name": "密尔沃基雄鹿", "city": "密尔沃基", "conference": "东部", "division": "中部"},
    "DEN": {"name": "丹佛掘金", "city": "丹佛", "conference": "西部", "division": "西北"},
    "PHX": {"name": "菲尼克斯太阳", "city": "菲尼克斯", "conference": "西部", "division": "太平洋"},
    "PHI": {"name": "费城76人", "city": "费城", "conference": "东部", "division": "大西洋"},
    "DAL": {"name": "达拉斯独行侠", "city": "达拉斯", "conference": "西部", "division": "西南"},
    "MEM": {"name": "孟菲斯灰熊", "city": "孟菲斯", "conference": "西部", "division": "西南"},
    "NYK": {"name": "纽约尼克斯", "city": "纽约", "conference": "东部", "division": "大西洋"},
    "SAC": {"name": "萨克拉门托国王", "city": "萨克拉门托", "conference": "西部", "division": "太平洋"},
    "CLE": {"name": "克利夫兰骑士", "city": "克利夫兰", "conference": "东部", "division": "中部"},
    "TOR": {"name": "多伦多猛龙", "city": "多伦多", "conference": "东部", "division": "大西洋"},
    "CHI": {"name": "芝加哥公牛", "city": "芝加哥", "conference": "东部", "division": "中部"},
    "ORL": {"name": "奥兰多魔术", "city": "奥兰多", "conference": "东部", "division": "东南"},
    "IND": {"name": "印第安纳步行者", "city": "印第安纳", "conference": "东部", "division": "中部"},
    "WAS": {"name": "华盛顿奇才", "city": "华盛顿", "conference": "东部", "division": "东南"},
    "ATL": {"name": "亚特兰大老鹰", "city": "亚特兰大", "conference": "东部", "division": "东南"},
    "CHA": {"name": "夏洛特黄蜂", "city": "夏洛特", "conference": "东部", "division": "东南"},
    "DET": {"name": "底特律活塞", "city": "底特律", "conference": "东部", "division": "中部"},
    "OKC": {"name": "俄克拉荷马雷霆", "city": "俄克拉荷马", "conference": "西部", "division": "西北"},
    "HOU": {"name": "休斯顿火箭", "city": "休斯顿", "conference": "西部", "division": "西南"},
    "NOP": {"name": "新奥尔良鹈鹕", "city": "新奥尔良", "conference": "西部", "division": "西南"},
    "UTA": {"name": "犹他爵士", "city": "盐湖城", "conference": "西部", "division": "西北"},
    "SAS": {"name": "圣安东尼奥马刺", "city": "圣安东尼奥", "conference": "西部", "division": "西南"},
    "MIN": {"name": "明尼苏达森林狼", "city": "明尼苏达", "conference": "西部", "division": "西北"},
    "POR": {"name": "波特兰开拓者", "city": "波特兰", "conference": "西部", "division": "西北"},
}

PLAYERS_DB = {
    "詹姆斯": {"en": "LeBron James", "team": "LAL", "position": "小前锋", "number": "23", "height": "206", "weight": "113", "year": "2003"},
    "库里": {"en": "Stephen Curry", "team": "GSW", "position": "控球后卫", "number": "30", "height": "188", "weight": "84", "year": "2009"},
    "杜兰特": {"en": "Kevin Durant", "team": "PHX", "position": "小前锋", "number": "35", "height": "208", "weight": "109", "year": "2007"},
    "字母哥": {"en": "Giannis Antetokounmpo", "team": "MIL", "position": "大前锋", "number": "34", "height": "211", "weight": "110", "year": "2013"},
    "约基奇": {"en": "Nikola Jokic", "team": "DEN", "position": "中锋", "number": "15", "height": "208", "weight": "113", "year": "2014"},
    "东契奇": {"en": "Luka Doncic", "team": "DAL", "position": "控球后卫", "number": "77", "height": "201", "weight": "104", "year": "2018"},
    "浓眉": {"en": "Anthony Davis", "team": "LAL", "position": "大前锋", "number": "3", "height": "208", "weight": "106", "year": "2012"},
    "戴维斯": {"en": "Anthony Davis", "team": "LAL", "position": "大前锋", "number": "3", "height": "208", "weight": "106", "year": "2012"},
    "哈登": {"en": "James Harden", "team": "LAC", "position": "得分后卫", "number": "1", "height": "196", "weight": "100", "year": "2009"},
    "威少": {"en": "Russell Westbrook", "team": "DEN", "position": "控球后卫", "number": "0", "height": "191", "weight": "91", "year": "2008"},
    "保罗": {"en": "Chris Paul", "team": "SAS", "position": "控球后卫", "number": "3", "height": "183", "weight": "79", "year": "2005"},
    "巴特勒": {"en": "Jimmy Butler", "team": "MIA", "position": "小前锋", "number": "22", "height": "201", "weight": "95", "year": "2011"},
    "伦纳德": {"en": "Kawhi Leonard", "team": "LAC", "position": "小前锋", "number": "2", "height": "201", "weight": "102", "year": "2011"},
    "乔治": {"en": "Paul George", "team": "PHI", "position": "小前锋", "number": "8", "height": "203", "weight": "99", "year": "2010"},
    "布朗": {"en": "Jaylen Brown", "team": "BOS", "position": "得分后卫", "number": "7", "height": "198", "weight": "101", "year": "2016"},
    "塔图姆": {"en": "Jayson Tatum", "team": "BOS", "position": "小前锋", "number": "0", "height": "203", "weight": "95", "year": "2017"},
    "恩比德": {"en": "Joel Embiid", "team": "PHI", "position": "中锋", "number": "21", "height": "213", "weight": "127", "year": "2014"},
    "布克": {"en": "Devin Booker", "team": "PHX", "position": "得分后卫", "number": "1", "height": "196", "weight": "93", "year": "2015"},
    "利拉德": {"en": "Damian Lillard", "team": "MIL", "position": "控球后卫", "number": "0", "height": "188", "weight": "88", "year": "2012"},
    "莫兰特": {"en": "Ja Morant", "team": "MEM", "position": "控球后卫", "number": "12", "height": "191", "weight": "79", "year": "2019"},
    "锡安": {"en": "Zion Williamson", "team": "NOP", "position": "大前锋", "number": "1", "height": "198", "weight": "128", "year": "2019"},
    "爱德华兹": {"en": "Anthony Edwards", "team": "MIN", "position": "得分后卫", "number": "5", "height": "193", "weight": "102", "year": "2020"},
    "亚历山大": {"en": "Shai Gilgeous-Alexander", "team": "OKC", "position": "控球后卫", "number": "2", "height": "198", "weight": "88", "year": "2018"},
    "福克斯": {"en": "De'Aaron Fox", "team": "SAC", "position": "控球后卫", "number": "5", "height": "191", "weight": "84", "year": "2017"},
    "华子": {"en": "Anthony Edwards", "team": "MIN", "position": "得分后卫", "number": "5", "height": "193", "weight": "102", "year": "2020"},
    "比尔": {"en": "Bradley Beal", "team": "PHX", "position": "得分后卫", "number": "3", "height": "193", "weight": "93", "year": "2012"},
    "拉文": {"en": "Zach LaVine", "team": "CHI", "position": "得分后卫", "number": "8", "height": "196", "weight": "91", "year": "2014"},
    "德罗赞": {"en": "DeMar DeRozan", "team": "CHI", "position": "小前锋", "number": "11", "height": "198", "weight": "100", "year": "2009"},
    "拉塞尔": {"en": "D'Angelo Russell", "team": "LAL", "position": "控球后卫", "number": "1", "height": "193", "weight": "88", "year": "2015"},
    "欧文": {"en": "Kyrie Irving", "team": "DAL", "position": "控球后卫", "number": "11", "height": "188", "weight": "88", "year": "2011"},
}

TEAM_IDS = {v["name"]: k for k, v in TEAM_INFO.items()}
for k, v in TEAM_INFO.items():
    TEAM_IDS[k] = k
    TEAM_IDS[v["city"]] = k

STANDINGS_DATA = {
    "东部": [
        {"team": "CLE", "wins": 45, "losses": 20},
        {"team": "BOS", "wins": 44, "losses": 22},
        {"team": "NYK", "wins": 42, "losses": 24},
        {"team": "MIA", "wins": 35, "losses": 30},
        {"team": "ORL", "wins": 35, "losses": 31},
        {"team": "CHI", "wins": 32, "losses": 33},
        {"team": "IND", "wins": 31, "losses": 34},
        {"team": "PHI", "wins": 30, "losses": 35},
        {"team": "TOR", "wins": 25, "losses": 40},
        {"team": "ATL", "wins": 24, "losses": 41},
    ],
    "西部": [
        {"team": "OKC", "wins": 48, "losses": 18},
        {"team": "DEN", "wins": 45, "losses": 21},
        {"team": "LAC", "wins": 42, "losses": 24},
        {"team": "MIN", "wins": 40, "losses": 26},
        {"team": "PHX", "wins": 39, "losses": 27},
        {"team": "LAL", "wins": 38, "losses": 28},
        {"team": "DAL", "wins": 36, "losses": 30},
        {"team": "SAC", "wins": 35, "losses": 31},
        {"team": "MEM", "wins": 32, "losses": 34},
        {"team": "GSW", "wins": 30, "losses": 35},
    ]
}

TEAM_SCHEDULE = [
    {"home": "LAL", "away": "GSW", "home_score": 112, "away_score": 108, "status": "已结束"},
    {"home": "BOS", "away": "MIA", "home_score": 118, "away_score": 105, "status": "已结束"},
    {"home": "DEN", "away": "PHX", "home_score": 125, "away_score": 118, "status": "已结束"},
    {"home": "OKC", "away": "MIN", "home_score": None, "away_score": None, "status": "即将进行", "time": "19:30"},
    {"home": "LAC", "away": "DAL", "home_score": None, "away_score": None, "status": "即将进行", "time": "22:00"},
    {"home": "NYK", "away": "PHI", "home_score": None, "away_score": None, "status": "明日"},
    {"home": "CLE", "away": "MIL", "home_score": None, "away_score": None, "status": "明日"},
]

def get_team_info(team_name):
    team_id = None
    for tid, info in TEAM_INFO.items():
        if team_name in info["name"] or team_name in info["city"] or team_name.lower() == tid.lower():
            team_id = tid
            break
    
    if team_id and team_id in TEAM_INFO:
        info = TEAM_INFO[team_id]
        return f"""{info['name']}
所在城市: {info['city']}
所属联盟: {info['conference']}联盟
所属分区: {info['division']}分区"""
    return f"未找到球队 {team_name} 的信息"

def get_player_info(player_name):
    if player_name in PLAYERS_DB:
        p = PLAYERS_DB[player_name]
        team_info = TEAM_INFO.get(p["team"], {})
        return f"""{player_name} ({p['en']})
球队: {team_info.get('name', '未知')}
球衣号码: {p['number']}
位置: {p['position']}
身高: {p['height']} cm
体重: {p['weight']} kg
选秀年份: {p['year']}年"""
    
    for cn_name, p in PLAYERS_DB.items():
        if p["en"].lower() == player_name.lower():
            team_info = TEAM_INFO.get(p["team"], {})
            return f"""{cn_name} ({p['en']})
球队: {team_info.get('name', '未知')}
球衣号码: {p['number']}
位置: {p['position']}
身高: {p['height']} cm
体重: {p['weight']} kg
选秀年份: {p['year']}年"""
    
    return f"未找到球员 {player_name} 的信息"

def get_standings():
    result = "🏆 2024-25赛季 NBA东西部排名\n\n"
    result += "=" * 35 + "\n"
    result += "【东部联盟】\n"
    result += "-" * 35 + "\n"
    for i, team in enumerate(STANDINGS_DATA["东部"], 1):
        tinfo = TEAM_INFO.get(team["team"], {})
        result += f"{i:2}. {tinfo.get('name', team['team']):12} {team['wins']}胜 {team['losses']}负\n"
    
    result += "\n" + "=" * 35 + "\n"
    result += "【西部联盟】\n"
    result += "-" * 35 + "\n"
    for i, team in enumerate(STANDINGS_DATA["西部"], 1):
        tinfo = TEAM_INFO.get(team["team"], {})
        result += f"{i:2}. {tinfo.get('name', team['team']):12} {team['wins']}胜 {team['losses']}负\n"
    
    return result

def get_today_games():
    result = "🏀 近期NBA比赛\n"
    result += "=" * 40 + "\n"
    
    for game in TEAM_SCHEDULE:
        home_info = TEAM_INFO.get(game["home"], {})
        away_info = TEAM_INFO.get(game["away"], {})
        home_name = home_info.get("name", game["home"])
        away_name = away_info.get("name", game["away"])
        
        if game["status"] == "已结束":
            result += f"{home_name} {game['home_score']} - {game['away_score']} {away_name}\n"
            result += f"   状态: {game['status']}\n\n"
        else:
            result += f"{away_name} @ {home_name}\n"
            result += f"   时间: {game.get('time', 'TBD')} | 状态: {game['status']}\n\n"
    
    return result

def get_team_schedule(team_name):
    team_id = None
    for tid, info in TEAM_INFO.items():
        if team_name in info["name"] or team_name in info["city"] or team_name.lower() == tid.lower():
            team_id = tid
            break
    
    if not team_id:
        return f"未找到球队 {team_name}"
    
    team_name_cn = TEAM_INFO.get(team_id, {}).get("name", team_name)
    result = f"📅 {team_name_cn} 近期赛程\n"
    result += "=" * 40 + "\n"
    
    found = False
    for game in TEAM_SCHEDULE:
        if game["home"] == team_id or game["away"] == team_id:
            found = True
            home_info = TEAM_INFO.get(game["home"], {})
            away_info = TEAM_INFO.get(game["away"], {})
            
            if game["status"] == "已结束":
                result += f"vs {away_info.get('name', game['away'])} {game['home_score']}-{game['away_score']} 已结束\n"
            else:
                result += f"vs {away_info.get('name', game['away'])} - {game.get('time', 'TBD')} {game['status']}\n"
    
    if not found:
        result += "暂无比赛信息"
    
    return result

def search_player(keyword):
    results = []
    for cn_name, p in PLAYERS_DB.items():
        if keyword in cn_name or keyword.lower() in p["en"].lower():
            results.append((cn_name, p))
    
    if not results:
        return f"未找到包含 '{keyword}' 的球员"
    
    result = f"🔍 找到 {len(results)} 名球员:\n\n"
    for cn_name, p in results[:5]:
        team_info = TEAM_INFO.get(p["team"], {})
        result += f"• {cn_name} ({p['en']}) - {team_info.get('name', '未知')} #{p['number']}\n"
    
    return result

def nba_api_query(query_type, params=None):
    if params is None:
        params = {}
    
    query_map = {
        "games": get_today_games,
        "standings": get_standings,
        "player": lambda: get_player_info(params.get("player_name", "")),
        "schedule": lambda: get_team_schedule(params.get("team_name", "")),
        "search": lambda: search_player(params.get("keyword", "")),
        "team": lambda: get_team_info(params.get("team_name", "")),
    }
    
    if query_type in query_map:
        return query_map[query_type]()
    else:
        return f"未知查询类型: {query_type}"

if __name__ == "__main__":
    print("=== NBA 数据测试 ===\n")
    print(get_today_games())
    print("\n" + "=" * 50)
    print(get_standings())
    print("\n" + "=" * 50)
    print(get_player_info("詹姆斯"))
    print("\n" + "=" * 50)
    print(get_team_schedule("湖人"))
