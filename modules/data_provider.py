#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import http.client

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from config import config
except ImportError:
    class Config:
        NBA_API_KEY = ""
        NBA_API_HOST = "nba-api-free-data.p.rapidapi.com"
        BALLDONTLIE_API_KEY = ""
        USE_BALLDONTLIE = True
        USE_NBA_API = True
    config = Config()


class DataProvider:
    """统一数据提供者，整合多个数据源"""
    
    def __init__(self):
        self.cache = {}
        self.cache_time = {}
        self.cache_ttl = 1800  # 30分钟缓存
        
    def _get_cache(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
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
        """设置缓存数据"""
        self.cache[key] = data
        self.cache_time[key] = datetime.now()
    
    # ==================== BallDontLie API (免费) ====================
    
    def _ball_dont_lie_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """请求 BallDontLie API"""
        try:
            url = f"https://api.balldontlie.io/v1/{endpoint}"
            headers = {}
            # 添加 API Key 如果有配置
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
        """从 BallDontLie 获取比赛"""
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
        """从 BallDontLie 获取球员"""
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
    
    def get_stats_bdl(self, player_ids: List[int] = None, game_ids: List[int] = None, 
                      dates: List[str] = None, per_page: int = 100) -> List[Dict]:
        """从 BallDontLie 获取统计数据"""
        cache_key = f"stats_bdl_{player_ids}_{game_ids}_{dates}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        params = {'per_page': per_page}
        if player_ids:
            params['player_ids[]'] = player_ids
        if game_ids:
            params['game_ids[]'] = game_ids
        if dates:
            params['dates[]'] = dates
        
        data = self._ball_dont_lie_request("stats", params)
        if data:
            stats = data.get('data', [])
            self._set_cache(cache_key, stats)
            return stats
        return []
    
    def get_standings_bdl(self) -> Dict:
        """从 BallDontLie 获取排名"""
        cache_key = "standings_bdl"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        # BallDontLie 没有直接的排名 API，需要通过球队数据计算
        data = self._ball_dont_lie_request("teams")
        if data:
            teams = data.get('data', [])
            self._set_cache(cache_key, teams)
            return teams
        return []
    
    # ==================== RapidAPI NBA ====================
    
    def _rapid_api_request(self, endpoint: str) -> Optional[Dict]:
        """请求 RapidAPI NBA"""
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
        """使用 nba_api 库获取数据"""
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
        """获取今日比赛（多数据源）"""
        cache_key = f"today_games_{datetime.now().strftime('%Y%m%d')}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        result = None
        
        # 尝试 nba_api
        if getattr(config, 'USE_NBA_API', True):
            try:
                data = self._get_nba_api_data("today_games")
                if data:
                    result = self._format_nba_api_games(data)
                    logger.info("使用 nba_api 获取今日比赛")
            except Exception as e:
                logger.warning(f"nba_api 获取比赛失败: {e}")
        
        # 尝试 BallDontLie
        if not result and getattr(config, 'USE_BALLDONTLIE', True):
            try:
                today = datetime.now().strftime('%Y-%m-%d')
                games = self.get_games_bdl(date=today)
                if games:
                    result = self._format_bdl_games(games)
                    logger.info("使用 BallDontLie 获取今日比赛")
            except Exception as e:
                logger.warning(f"BallDontLie 获取比赛失败: {e}")
        
        if result:
            self._set_cache(cache_key, result)
            return result
        
        return "🏀 今日暂无比赛数据或获取失败"
    
    def get_standings(self) -> str:
        """获取排名（多数据源）"""
        cache_key = "standings"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        result = None
        
        # 尝试 nba_api
        if getattr(config, 'USE_NBA_API', True):
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
        
        return "🏆 排名数据获取失败"
    
    def get_player_info(self, player_name: str) -> str:
        """获取球员信息（多数据源）"""
        cache_key = f"player_{player_name}"
        cached = self._get_cache(cache_key)
        if cached:
            return cached
        
        # 尝试 BallDontLie 搜索
        if getattr(config, 'USE_BALLDONTLIE', True):
            try:
                players = self.get_players_bdl(search=player_name)
                if players:
                    result = self._format_bdl_player(players[0])
                    self._set_cache(cache_key, result)
                    return result
            except Exception as e:
                logger.warning(f"BallDontLie 获取球员失败: {e}")
        
        return f"未找到球员 {player_name} 的信息"
    
    def search_players(self, query: str) -> List[Dict]:
        """搜索球员"""
        # 优先使用 BallDontLie
        if getattr(config, 'USE_BALLDONTLIE', True):
            players = self.get_players_bdl(search=query)
            if players:
                return players
        
        # 使用 nba_api
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
    
    def _format_nba_api_games(self, data: Dict) -> str:
        """格式化 nba_api 比赛数据"""
        result = "🏀 今日NBA比赛\n"
        result += "=" * 40 + "\n"
        
        try:
            # 解析 nba_api 返回的数据
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
        """格式化 BallDontLie 比赛数据"""
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
        """格式化 nba_api 排名数据"""
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
        """格式化 BallDontLie 球员数据"""
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


# 全局数据提供者实例
data_provider = DataProvider()


# 便捷函数

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
    
    # 测试 BallDontLie
    print("1. 测试 BallDontLie - 获取今日比赛")
    games = data_provider.get_today_games()
    print(games)
    
    print("\n2. 测试 BallDontLie - 搜索球员")
    players = data_provider.search_players("LeBron")
    for p in players[:3]:
        print(f"  - {p.get('full_name', p.get('first_name', '') + ' ' + p.get('last_name', ''))}")
    
    print("\n3. 测试排名")
    standings = data_provider.get_standings()
    print(standings[:500] if len(standings) > 500 else standings)
