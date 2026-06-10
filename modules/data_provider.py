#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import http.client
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEAM_NAME_CN = {
    'Atlanta Hawks': '亚特兰大老鹰', 'Boston Celtics': '波士顿凯尔特人',
    'Brooklyn Nets': '布鲁克林篮网', 'Charlotte Hornets': '夏洛特黄蜂',
    'Chicago Bulls': '芝加哥公牛', 'Cleveland Cavaliers': '克利夫兰骑士',
    'Dallas Mavericks': '达拉斯独行侠', 'Denver Nuggets': '丹佛掘金',
    'Detroit Pistons': '底特律活塞', 'Golden State Warriors': '金州勇士',
    'Houston Rockets': '休斯顿火箭', 'Indiana Pacers': '印第安纳步行者',
    'LA Clippers': '洛杉矶快船', 'Los Angeles Lakers': '洛杉矶湖人',
    'Memphis Grizzlies': '孟菲斯灰熊', 'Miami Heat': '迈阿密热火',
    'Milwaukee Bucks': '密尔沃基雄鹿', 'Minnesota Timberwolves': '明尼苏达森林狼',
    'New Orleans Pelicans': '新奥尔良鹈鹕', 'New York Knicks': '纽约尼克斯',
    'Oklahoma City Thunder': '俄克拉荷马城雷霆', 'Orlando Magic': '奥兰多魔术',
    'Philadelphia 76ers': '费城76人', 'Phoenix Suns': '菲尼克斯太阳',
    'Portland Trail Blazers': '波特兰开拓者', 'Sacramento Kings': '萨克拉门托国王',
    'San Antonio Spurs': '圣安东尼奥马刺', 'Toronto Raptors': '多伦多猛龙',
    'Utah Jazz': '犹他爵士', 'Washington Wizards': '华盛顿奇才',
}

STATUS_CN = {
    'Scheduled': '未开始', 'In Progress': '进行中', 'Halftime': '中场休息',
    'Final': '已结束', 'Postponed': '延期', 'Canceled': '取消',
}

WEEKDAY_CN = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

CITY_NAME_CN = {
    'San Antonio': '圣安东尼奥', 'New York': '纽约', 'Los Angeles': '洛杉矶',
    'Boston': '波士顿', 'Chicago': '芝加哥', 'Miami': '迈阿密',
    'Houston': '休斯顿', 'Dallas': '达拉斯', 'Denver': '丹佛',
    'Phoenix': '菲尼克斯', 'Portland': '波特兰', 'Sacramento': '萨克拉门托',
    'Atlanta': '亚特兰大', 'Brooklyn': '布鲁克林', 'Charlotte': '夏洛特',
    'Cleveland': '克利夫兰', 'Detroit': '底特律', 'Indiana': '印第安纳',
    'Memphis': '孟菲斯', 'Milwaukee': '密尔沃基', 'Minneapolis': '明尼阿波利斯',
    'New Orleans': '新奥尔良', 'Oklahoma City': '俄克拉荷马城', 'Orlando': '奥兰多',
    'Philadelphia': '费城', 'Salt Lake City': '盐湖城', 'Toronto': '多伦多',
    'Washington': '华盛顿', 'San Francisco': '旧金山', 'Oakland': '奥克兰',
}

try:
    from config import config
except ImportError:
    class Config:
        NBA_API_KEY = ""
        NBA_API_HOST = "nba-api-free-data.p.rapidapi.com"
        BALLDONTLIE_API_KEY = ""
        USE_BALLDONTLIE = True
        USE_NBA_API = True
        USE_ESPN = True
        USE_THESPORTSDB = True
    config = Config()


class DataProvider:
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_ttl = 1800

    def _get_cache(self, key: str) -> Optional[Any]:
        if key in self.cache:
            cached_time = self.cache_time.get(key)
            if cached_time and (datetime.now() - cached_time).seconds < self.cache_ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                if key in self.cache_time:
                    del self.cache_time[key]
        return None

    def _set_cache(self, key: str, data: Any):
        self.cache[key] = data
        self.cache_time[key] = datetime.now()

    # ==================== ESPN API (免费，无需Key) ====================

    def _espn_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/{endpoint}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"ESPN API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"ESPN request failed: {e}")
            return None

    def get_games_espn(self) -> List[Dict]:
        cache_key = "games_espn"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._espn_request("scoreboard")
        if data:
            events = data.get('events', [])
            self._set_cache(cache_key, events)
            return events
        return []

    def get_upcoming_games_espn(self, days: int = 7) -> List[Dict]:
        """获取未来几天的比赛"""
        all_events = []
        for i in range(1, days + 1):
            date = (datetime.now() + timedelta(days=i)).strftime('%Y%m%d')
            data = self._espn_request("scoreboard", params={'dates': date})
            if data:
                events = data.get('events', [])
                if events:
                    for event in events:
                        event['_future_date'] = date
                    all_events.extend(events)
                    if len(all_events) >= 10:
                        break
        return all_events[:10]

    def get_standings_espn(self) -> Dict:
        cache_key = "standings_espn"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._espn_request("standings")
        if data:
            self._set_cache(cache_key, data)
            return data
        return {}

    def get_player_info_espn(self, player_name: str) -> Optional[Dict]:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/athletes/search"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            params = {'query': player_name, 'limit': 1}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                athletes = data.get('athletes', [])
                if athletes:
                    return athletes[0]
            return None
        except Exception as e:
            logger.error(f"ESPN player search failed: {e}")
            return None

    def get_player_info_espn_v2(self, player_name: str) -> Optional[Dict]:
        try:
            url = f"https://site.web.api.espn.com/apis/common/v3/sports/basketball/nba/athletes/search"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            params = {'query': player_name, 'limit': 1}
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                athletes = data.get('items', [])
                if athletes:
                    return athletes[0]
            return None
        except Exception as e:
            logger.error(f"ESPN player search v2 failed: {e}")
            return None

    def get_espn_news(self, limit: int = 5) -> List[Dict]:
        cache_key = f"espn_news_{limit}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._espn_request("news", params={'limit': limit})
        if data:
            articles = data.get('articles', [])
            self._set_cache(cache_key, articles)
            return articles
        return []

    def get_espn_team_list(self) -> List[Dict]:
        cache_key = "espn_teams"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._espn_request("teams")
        if data:
            sports = data.get('sports', [])
            if sports:
                leagues = sports[0].get('leagues', [])
                if leagues:
                    teams = leagues[0].get('teams', [])
                    self._set_cache(cache_key, teams)
                    return teams
        return []

    def get_espn_game_summary(self, event_id: str) -> Optional[Dict]:
        cache_key = f"espn_game_{event_id}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._espn_request("summary", params={'event': event_id})
        if data:
            self._set_cache(cache_key, data)
            return data
        return None

    # ==================== TheSportsDB API (免费，无需Key) ====================

    def _thesportsdb_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        try:
            url = f"https://www.thesportsdb.com/api/v1/json/3/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"TheSportsDB API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"TheSportsDB request failed: {e}")
            return None

    def get_games_thesportsdb(self) -> List[Dict]:
        cache_key = "thesportsdb_games"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        # NBA League ID: 4387
        # 获取未来比赛
        data = self._thesportsdb_request("eventsnextleague.php", params={'id': '4387'})
        if data:
            events = data.get('events', []) or []
            self._set_cache(cache_key, events)
            return events
        return []

    def get_recent_games_thesportsdb(self) -> List[Dict]:
        cache_key = "thesportsdb_recent_games"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._thesportsdb_request("eventslastleague.php", params={'id': '4387'})
        if data:
            events = data.get('events', []) or []
            self._set_cache(cache_key, events)
            return events
        return []

    def get_team_thesportsdb(self, team_name: str) -> Optional[Dict]:
        cache_key = f"thesportsdb_team_{team_name}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._thesportsdb_request("searchteams.php", params={'t': team_name})
        if data:
            teams = data.get('teams', [])
            if teams:
                # 过滤NBA球队
                nba_teams = [t for t in teams if 'NBA' in t.get('strLeague', '') or 'Basketball' in t.get('strSport', '')]
                if nba_teams:
                    result = nba_teams[0]
                    self._set_cache(cache_key, result)
                    return result
        return None

    def get_player_thesportsdb(self, player_name: str) -> Optional[Dict]:
        cache_key = f"thesportsdb_player_{player_name}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._thesportsdb_request("searchplayers.php", params={'p': player_name})
        if data:
            players = data.get('players', [])
            if players:
                # 过滤NBA球员
                nba_players = [p for p in players if 'NBA' in p.get('strLeague', '') or 'Basketball' in p.get('strSport', '')]
                if nba_players:
                    result = nba_players[0]
                    self._set_cache(cache_key, result)
                    return result
        return None

    # ==================== BallDontLie API ====================

    def _ball_dont_lie_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        try:
            url = f"https://api.balldontlie.io/v1/{endpoint}"
            headers = {}
            api_key = getattr(config, 'BALLDONTLIE_API_KEY', None)
            if api_key:
                headers['Authorization'] = api_key
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"BallDontLie API error: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"BallDontLie request failed: {e}")
            return None

    def get_games_bdl(self, date: str = None, team_ids: List[int] = None) -> List[Dict]:
        cache_key = f"games_bdl_{date}_{team_ids}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        params = {}
        if date:
            params['dates[]'] = date
        if team_ids:
            params['team_ids[]'] = team_ids

        data = self._ball_dont_lie_request("games", params)
        if data:
            games = data.get('data', [])
            self._set_cache(cache_key, games)
            return games
        return []

    def get_players_bdl(self, search: str = None, per_page: int = 100) -> List[Dict]:
        cache_key = f"players_bdl_{search}_{per_page}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        params = {'per_page': per_page}
        if search:
            params['search'] = search

        data = self._ball_dont_lie_request("players", params)
        if data:
            players = data.get('data', [])
            self._set_cache(cache_key, players)
            return players
        return []

    def get_standings_bdl(self) -> Dict:
        cache_key = "standings_bdl"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        data = self._ball_dont_lie_request("teams")
        if data:
            teams = data.get('data', [])
            self._set_cache(cache_key, teams)
            return teams
        return []

    # ==================== RapidAPI NBA ====================

    def _rapid_api_request(self, endpoint: str) -> Optional[Dict]:
        if not getattr(config, 'NBA_API_KEY', None):
            return None

        try:
            conn = http.client.HTTPSConnection(config.NBA_API_HOST)
            headers = {
                "x-rapidapi-key": config.NBA_API_KEY,
                "x-rapidapi-host": config.NBA_API_HOST,
                "Content-Type": "application/json"
            }
            conn.request("GET", endpoint, headers=headers)
            res = conn.getresponse()
            data = res.read()
            conn.close()

            if res.status == 200:
                return json.loads(data.decode("utf-8"))
            else:
                logger.warning(f"RapidAPI error {res.status}")
                return None
        except Exception as e:
            logger.error(f"RapidAPI request failed: {e}")
            return None

    # ==================== nba_api (Python库) ====================

    def _get_nba_api_data(self, method: str, **kwargs) -> Optional[Any]:
        try:
            from nba_api.stats.endpoints import scoreboardv2, leaguestandings, commonplayerinfo
            from nba_api.stats.static import players, teams

            if method == "today_games":
                today = datetime.now().strftime('%Y-%m-%d')
                scoreboard = scoreboardv2.ScoreboardV2(game_date=today)
                return scoreboard.get_dict()

            elif method == "standings":
                standings = leaguestandings.LeagueStandings()
                return standings.get_dict()

            elif method == "player_info":
                player_name = kwargs.get('name')
                player_list = players.find_players_by_full_name(player_name)
                if player_list:
                    player_id = player_list[0]['id']
                    info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
                    return info.get_dict()
                return None

            elif method == "all_players":
                return players.get_players()

            elif method == "all_teams":
                return teams.get_teams()

        except ImportError:
            logger.warning("nba_api 库未安装")
            return None
        except Exception as e:
            logger.error(f"nba_api error: {e}")
            return None

    # ==================== 统一接口 ====================

    def get_today_games(self) -> str:
        cache_key = f"today_games_{datetime.now().strftime('%Y%m%d')}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        result = None

        if getattr(config, 'USE_ESPN', True):
            try:
                games = self.get_games_espn()
                if games:
                    result = self._format_espn_games(games, is_future=False)
                    logger.info("使用 ESPN API 获取今日比赛")
                else:
                    upcoming = self.get_upcoming_games_espn()
                    if upcoming:
                        result = self._format_espn_games(upcoming, is_future=True)
                        logger.info("今日无比赛，显示近期赛程")
            except Exception as e:
                logger.warning(f"ESPN 获取比赛失败: {e}")

        if not result and getattr(config, 'USE_NBA_API', True):
            try:
                data = self._get_nba_api_data("today_games")
                if data:
                    result = self._format_nba_api_games(data)
                    logger.info("使用 nba_api 获取今日比赛")
            except Exception as e:
                logger.warning(f"nba_api 获取比赛失败: {e}")

        if not result and getattr(config, 'USE_BALLDONTLIE', True):
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                games = self.get_games_bdl(date=today)
                if games:
                    result = self._format_bdl_games(games)
                    logger.info("使用 BallDontLie 获取今日比赛")
            except Exception as e:
                logger.warning(f"BallDontLie 获取比赛失败: {e}")

        if not result and getattr(config, 'USE_THESPORTSDB', True):
            try:
                future_games = self.get_games_thesportsdb()
                recent_games = self.get_recent_games_thesportsdb()
                all_games = recent_games + future_games
                if all_games:
                    result = self._format_thesportsdb_games(all_games)
                    logger.info("使用 TheSportsDB 获取比赛")
            except Exception as e:
                logger.warning(f"TheSportsDB 获取比赛失败: {e}")

        if result:
            self._set_cache(cache_key, result)
            return result

        return "🏀 今日暂无比赛数据或获取失败"

    def get_standings(self) -> str:
        cache_key = "standings"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        result = None

        if getattr(config, 'USE_ESPN', True):
            try:
                data = self.get_standings_espn()
                if data and data.get('standings'):
                    result = self._format_espn_standings(data)
                    logger.info("使用 ESPN API 获取排名")
            except Exception as e:
                logger.warning(f"ESPN 获取排名失败: {e}")

        if not result and getattr(config, 'USE_NBA_API', True):
            try:
                data = self._get_nba_api_data("standings")
                if data:
                    result = self._format_nba_api_standings(data)
                    logger.info("使用 nba_api 获取排名")
            except Exception as e:
                logger.warning(f"nba_api 获取排名失败: {e}")

        if result:
            self._set_cache(cache_key, result)
            return result

        from modules.nba_data import get_standings as get_local_standings
        return get_local_standings()

    def get_player_info(self, player_name: str) -> str:
        cache_key = f"player_{player_name}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        if getattr(config, 'USE_ESPN', True):
            try:
                player = self.get_player_info_espn(player_name)
                if player:
                    result = self._format_espn_player(player)
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e:
                logger.warning(f"ESPN 获取球员失败: {e}")

        if getattr(config, 'USE_BALLDONTLIE', True):
            try:
                players = self.get_players_bdl(search=player_name)
                if players:
                    result = self._format_bdl_player(players[0])
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e:
                logger.warning(f"BallDontLie 获取球员失败: {e}")

        if getattr(config, 'USE_THESPORTSDB', True):
            try:
                player = self.get_player_thesportsdb(player_name)
                if player:
                    result = self._format_thesportsdb_player(player)
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e:
                logger.warning(f"TheSportsDB 获取球员失败: {e}")

        from modules.nba_data import get_player_info as get_local_player_info
        return get_local_player_info(player_name)

    def search_players(self, query: str) -> List[Dict]:
        if getattr(config, 'USE_ESPN', True):
            try:
                player = self.get_player_info_espn(query)
                if player:
                    return [player]
            except Exception as e:
                logger.warning(f"ESPN 搜索球员失败: {e}")

        if getattr(config, 'USE_BALLDONTLIE', True):
            players = self.get_players_bdl(search=query)
            if players:
                return players

        if getattr(config, 'USE_NBA_API', True):
            try:
                from nba_api.stats.static import players
                all_players = players.get_players()
                matches = [p for p in all_players if query.lower() in p['full_name'].lower()]
                return matches[:10]
            except Exception as e:
                logger.warning(f"nba_api 搜索球员失败: {e}")

        return []

    # ==================== 格式化方法 ====================

    def _translate_team_name(self, name_en: str) -> str:
        return TEAM_NAME_CN.get(name_en, name_en)

    def _translate_status(self, status_en: str) -> str:
        return STATUS_CN.get(status_en, status_en)

    def _parse_espn_time(self, detail: str, date_str: str = '') -> str:
        match = re.search(r'(\w+),\s*([A-Za-z]+)\s*(\d+)(?:st|nd|rd|th)?\s+at\s+(\d+):(\d+)\s*(AM|PM)', detail)
        if match:
            weekday_en, month_en, day, hour, minute, ampm = match.groups()
            month_map = {'January': '1月', 'February': '2月', 'March': '3月', 'April': '4月', 'May': '5月', 'June': '6月',
                         'July': '7月', 'August': '8月', 'September': '9月', 'October': '10月', 'November': '11月', 'December': '12月',
                         'Jan': '1月', 'Feb': '2月', 'Mar': '3月', 'Apr': '4月', 'Jun': '6月',
                         'Jul': '7月', 'Aug': '8月', 'Sep': '9月', 'Oct': '10月', 'Nov': '11月', 'Dec': '12月'}
            weekday_map = {'Monday': '周一', 'Tuesday': '周二', 'Wednesday': '周三', 'Thursday': '周四',
                           'Friday': '周五', 'Saturday': '周六', 'Sunday': '周日',
                           'Mon': '周一', 'Tue': '周二', 'Wed': '周三', 'Thu': '周四',
                           'Fri': '周五', 'Sat': '周六', 'Sun': '周日'}
            month_cn = month_map.get(month_en, month_en)
            weekday_cn = weekday_map.get(weekday_en, weekday_en)
            hour = int(hour)
            if ampm == 'PM' and hour != 12:
                hour += 12
            elif ampm == 'AM' and hour == 12:
                hour = 0
            return f"{month_cn}{day}日 {weekday_cn} {hour:02d}:{minute}"

        if date_str:
            try:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                dt_local = dt + timedelta(hours=8)
                weekday = WEEKDAY_CN[dt_local.weekday()]
                return f"{dt_local.month}月{dt_local.day}日 {weekday} {dt_local.hour:02d}:{dt_local.minute:02d} (北京时间)"
            except:
                pass
        return detail

    def _translate_city(self, city_en: str) -> str:
        return CITY_NAME_CN.get(city_en, city_en)

    def _format_single_game(self, event: Dict, is_future: bool = False) -> str:
        competitions = event.get('competitions', [])
        if not competitions:
            return ''
        comp = competitions[0]
        competitors = comp.get('competitors', [])
        if len(competitors) < 2:
            return ''

        away = competitors[0]
        home = competitors[1]
        away_name = self._translate_team_name(away.get('team', {}).get('displayName', 'TBD'))
        home_name = self._translate_team_name(home.get('team', {}).get('displayName', 'TBD'))
        away_score = away.get('score', '')
        home_score = home.get('score', '')

        status = event.get('status', {})
        status_type = status.get('type', {})
        status_desc = self._translate_status(status_type.get('description', '未知'))
        status_detail = status_type.get('detail', '')

        result = f"{away_name} @ {home_name}\n"
        if away_score and home_score:
            result += f"比分: {away_score} - {home_score}\n"

        if is_future:
            date_str = event.get('date', '')
            time_cn = self._parse_espn_time(status_detail, date_str)
            result += f"时间: {time_cn}\n"
        else:
            result += f"状态: {status_desc}"
            if status_detail:
                time_cn = self._parse_espn_time(status_detail)
                result += f" ({time_cn})"
            result += "\n"

        venue = comp.get('venue', {})
        if venue:
            city = self._translate_city(venue.get('address', {}).get('city', ''))
            arena = venue.get('fullName', '')
            if city or arena:
                result += f"地点: {arena} ({city})\n"

        result += "-" * 40 + "\n"
        return result

    def _format_espn_games(self, events: List[Dict], is_future: bool = False) -> str:
        if is_future:
            result = "🏀 近期NBA赛程\n"
        else:
            result = "🏀 今日NBA比赛\n"
        result += "=" * 40 + "\n"

        if not events:
            if is_future:
                result += "近期暂无赛程安排\n"
            else:
                result += "今日暂无比赛\n"
            return result

        for event in events:
            result += self._format_single_game(event, is_future)

        return result

    def _format_espn_standings(self, data: Dict) -> str:
        result = "🏆 NBA实时排名\n\n"

        try:
            standings = data.get('standings', [])
            if not standings:
                return result + "暂无排名数据\n"

            for entry in standings:
                conference = entry.get('name', '')
                standings_data = entry.get('entries', [])

                result += f"【{conference}】\n"
                result += "-" * 40 + "\n"
                for i, team in enumerate(standings_data[:15], 1):
                    team_info = team.get('team', {})
                    name = team_info.get('displayName', team_info.get('shortDisplayName', '未知'))
                    stats = team.get('stats', [])
                    wins = 0
                    losses = 0
                    win_pct = 0
                    for s in stats:
                        if s.get('name') == 'wins':
                            wins = s.get('value', 0)
                        elif s.get('name') == 'losses':
                            losses = s.get('value', 0)
                        elif s.get('name') == 'winPercent':
                            win_pct = s.get('value', 0)

                    result += f"{i:2}. {name:15} {wins:2}胜 {losses:2}负 ({win_pct:.3f})\n"

                result += "\n"

        except Exception as e:
            logger.error(f"格式化ESPN排名数据失败: {e}")
            result += "数据解析失败\n"

        return result

    def _format_espn_player(self, player: Dict) -> str:
        name = player.get('displayName', '未知')
        team = player.get('team', {}).get('displayName', '未知')
        position = player.get('position', {}).get('displayName', '未知')
        jersey = player.get('jersey', '未知')
        height = player.get('displayHeight', '未知')
        weight = player.get('displayWeight', '未知')
        age = player.get('age', '未知')

        result = f" {name}\n"
        result += "=" * 40 + "\n"
        result += f"球队: {team}\n"
        result += f"位置: {position}\n"
        result += f"身高: {height}\n"
        result += f"体重: {weight}\n"
        result += f"球衣号码: {jersey}\n"
        result += f"年龄: {age}\n"

        return result

    def _format_nba_api_games(self, data: Dict) -> str:
        result = "🏀 今日NBA比赛\n"
        result += "=" * 40 + "\n"

        try:
            result_sets = data.get('resultSets', [])
            if result_sets:
                headers = result_sets[0].get('headers', [])
                rows = result_sets[0].get('rowSet', [])

                for row in rows:
                    game_data = dict(zip(headers, row))
                    home_team = game_data.get('HOME_TEAM_NAME', 'TBD')
                    away_team = game_data.get('VISITOR_TEAM_NAME', 'TBD')
                    home_score = game_data.get('HOME_TEAM_PTS', 0)
                    away_score = game_data.get('VISITOR_TEAM_PTS', 0)
                    status = game_data.get('GAME_STATUS_TEXT', '未开始')

                    result += f"{away_team} @ {home_team}\n"
                    result += f"比分: {away_score} - {home_score}\n"
                    result += f"状态: {status}\n"
                    result += "-" * 40 + "\n"
        except Exception as e:
            logger.error(f"格式化比赛数据失败: {e}")
            result += "数据解析失败\n"

        return result

    def _format_bdl_games(self, games: List[Dict]) -> str:
        result = "🏀 今日NBA比赛\n"
        result += "=" * 40 + "\n"

        for game in games:
            home_team = game.get('home_team', {}).get('full_name', 'TBD')
            away_team = game.get('visitor_team', {}).get('full_name', 'TBD')
            home_score = game.get('home_team_score', 0)
            away_score = game.get('visitor_team_score', 0)
            status = game.get('status', '未开始')
            time = game.get('time', '')

            result += f"{away_team} @ {home_team}\n"
            if home_score or away_score:
                result += f"比分: {away_score} - {home_score}\n"
            result += f"状态: {status}"
            if time:
                result += f" {time}"
            result += "\n" + "-" * 40 + "\n"

        return result

    def _format_nba_api_standings(self, data: Dict) -> str:
        result = "🏆 NBA实时排名\n\n"

        try:
            result_sets = data.get('resultSets', [])
            if result_sets:
                headers = result_sets[0].get('headers', [])
                rows = result_sets[0].get('rowSet', [])

                east_teams = []
                west_teams = []

                for row in rows:
                    team_data = dict(zip(headers, row))
                    conference = team_data.get('Conference', '')
                    team_info = {
                        'name': team_data.get('TeamName', team_data.get('TeamCity', '')),
                        'wins': team_data.get('WINS', 0),
                        'losses': team_data.get('LOSSES', 0),
                        'win_pct': team_data.get('WinPCT', 0)
                    }

                    if 'East' in conference:
                        east_teams.append(team_info)
                    else:
                        west_teams.append(team_info)

                result += "【东部联盟】\n"
                result += "-" * 40 + "\n"
                for i, team in enumerate(east_teams[:15], 1):
                    result += f"{i:2}. {team['name']:15} {team['wins']:2}胜 {team['losses']:2}负 ({team['win_pct']:.3f})\n"

                result += "\n【西部联盟】\n"
                result += "-" * 40 + "\n"
                for i, team in enumerate(west_teams[:15], 1):
                    result += f"{i:2}. {team['name']:15} {team['wins']:2}胜 {team['losses']:2}负 ({team['win_pct']:.3f})\n"
        except Exception as e:
            logger.error(f"格式化排名数据失败: {e}")
            result += "数据解析失败\n"

        return result

    def _format_bdl_player(self, player: Dict) -> str:
        name = player.get('first_name', '') + ' ' + player.get('last_name', '')
        team = player.get('team', {}).get('full_name', '未知')
        position = player.get('position', '未知')
        height = player.get('height', '未知')
        weight = player.get('weight', '未知')
        jersey = player.get('jersey_number', '未知')

        result = f"🏀 {name}\n"
        result += f"球队: {team}\n"
        result += f"位置: {position}\n"
        result += f"身高: {height}\n"
        result += f"体重: {weight}\n"
        result += f"球衣号码: {jersey}\n"

        return result

    def _format_thesportsdb_games(self, games: List[Dict]) -> str:
        result = "🏀 NBA比赛\n"
        result += "=" * 40 + "\n"

        if not games:
            result += "暂无比赛数据\n"
            return result

        for game in games[:10]:
            home_team = game.get('strHomeTeam', 'TBD')
            away_team = game.get('strAwayTeam', 'TBD')
            home_score = game.get('intHomeScore', '')
            away_score = game.get('intAwayScore', '')
            date = game.get('dateEvent', '')
            time = game.get('strTime', '')
            status = game.get('strStatus', '未知')
            venue = game.get('strVenue', '')

            result += f"{away_team} @ {home_team}\n"
            if home_score and away_score:
                result += f"比分: {away_score} - {home_score}\n"
            if date:
                result += f"日期: {date}"
                if time:
                    result += f" {time}"
                result += "\n"
            if venue:
                result += f"场馆: {venue}\n"
            result += "-" * 40 + "\n"

        return result

    def _format_thesportsdb_player(self, player: Dict) -> str:
        name = player.get('strPlayer', '未知')
        team = player.get('strTeam', '未知')
        position = player.get('strPosition', '未知')
        height = player.get('strHeight', '未知')
        weight = player.get('strWeight', '未知')
        jersey = player.get('strNumber', '未知')
        birth = player.get('dateBorn', '未知')
        nationality = player.get('strNationality', '未知')

        result = f"🏀 {name}\n"
        result += "=" * 40 + "\n"
        result += f"球队: {team}\n"
        result += f"位置: {position}\n"
        result += f"身高: {height}\n"
        result += f"体重: {weight}\n"
        result += f"球衣号码: {jersey}\n"
        result += f"出生日期: {birth}\n"
        result += f"国籍: {nationality}\n"

        return result


data_provider = DataProvider()


def get_today_games() -> str:
    return data_provider.get_today_games()


def get_standings() -> str:
    return data_provider.get_standings()


def get_player_info(player_name: str) -> str:
    return data_provider.get_player_info(player_name)


def search_players(query: str) -> List[Dict]:
    return data_provider.search_players(query)


if __name__ == "__main__":
    print("=== 数据提供者测试 ===\n")

    print("1. 测试 ESPN API - 获取今日比赛")
    games = data_provider.get_today_games()
    print(games)

    print("\n2. 测试 ESPN API - 搜索球员")
    info = data_provider.get_player_info("LeBron")
    print(info)

    print("\n3. 测试 ESPN API - 排名")
    standings = data_provider.get_standings()
    print(standings[:500] if len(standings) > 500 else standings)
