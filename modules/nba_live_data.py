#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from nba_api.stats.endpoints import (
        playercareerstats,
        leaguestandings,
        scoreboardv2,
        commonplayerinfo,
        playergamelog,
        leagueleaders,
        teamgamelog
    )
    from nba_api.stats.static import players, teams
    NBA_API_AVAILABLE = True
    logger.info("nba_api 库已加载，实时数据功能可用")
except ImportError:
    NBA_API_AVAILABLE = False
    logger.warning("nba_api 库未安装，将使用本地静态数据。运行: pip install nba_api")

from config import TEAM_NAMES, config


@dataclass
class CacheItem:
    data: Any
    timestamp: datetime
    ttl: int = 1800
    
    def is_expired(self) -> bool:
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl


class DataCache:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._cache = {}
        return cls._instance
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            item = self._cache[key]
            if not item.is_expired():
                return item.data
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, data: Any, ttl: int = None):
        ttl = ttl or config.CACHE_TTL
        self._cache[key] = CacheItem(data=data, timestamp=datetime.now(), ttl=ttl)
    
    def clear(self):
        self._cache.clear()


cache = DataCache()


def get_team_id(team_name: str) -> Optional[int]:
    if not NBA_API_AVAILABLE:
        return None
    
    team_list = teams.get_teams()
    team_name_lower = team_name.lower()
    
    for team in team_list:
        full_name = team.get('full_name', '').lower()
        nickname = team.get('nickname', '').lower()
        abbreviation = team.get('abbreviation', '').lower()
        
        if (team_name_lower in full_name or 
            team_name_lower in nickname or 
            team_name_lower == abbreviation):
            return team.get('id')
    
    return None


def get_player_id(player_name: str) -> Optional[int]:
    if not NBA_API_AVAILABLE:
        return None
    
    player_list = players.find_players_by_full_name(player_name)
    if player_list:
        return player_list[0].get('id')
    
    all_players = players.get_players()
    player_name_lower = player_name.lower()
    
    for player in all_players:
        if player_name_lower in player.get('full_name', '').lower():
            return player.get('id')
    
    return None


def get_standings_live() -> str:
    cache_key = "standings"
    cached = cache.get(cache_key)
    if cached:
        logger.info("使用缓存的排名数据")
        return cached
    
    if not NBA_API_AVAILABLE:
        return get_standings_local()
    
    try:
        logger.info("从NBA API获取实时排名...")
        standings = leaguestandings.LeagueStandings()
        data = standings.get_dict()
        
        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        
        east_teams = []
        west_teams = []
        
        for row in rows:
            team_data = dict(zip(headers, row))
            conference = team_data.get('Conference', '')
            team_name = team_data.get('TeamName', team_data.get('TeamCity', ''))
            wins = team_data.get('WINS', 0)
            losses = team_data.get('LOSSES', 0)
            
            team_info = {
                'name': team_name,
                'wins': wins,
                'losses': losses,
                'win_pct': team_data.get('WinPCT', 0)
            }
            
            if 'East' in conference:
                east_teams.append(team_info)
            else:
                west_teams.append(team_info)
        
        result = "🏆 NBA实时排名\n\n"
        result += "=" * 40 + "\n"
        result += "【东部联盟】\n"
        result += "-" * 40 + "\n"
        for i, team in enumerate(east_teams[:15], 1):
            result += f"{i:2}. {team['name']:15} {team['wins']:2}胜 {team['losses']:2}负 ({team['win_pct']:.3f})\n"
        
        result += "\n" + "=" * 40 + "\n"
        result += "【西部联盟】\n"
        result += "-" * 40 + "\n"
        for i, team in enumerate(west_teams[:15], 1):
            result += f"{i:2}. {team['name']:15} {team['wins']:2}胜 {team['losses']:2}负 ({team['win_pct']:.3f})\n"
        
        cache.set(cache_key, result, ttl=1800)
        return result
        
    except Exception as e:
        logger.error(f"获取实时排名失败: {e}")
        return get_standings_local()


def get_today_games_live() -> str:
    cache_key = f"games_{datetime.now().strftime('%Y%m%d')}"
    cached = cache.get(cache_key)
    if cached:
        logger.info("使用缓存的比赛数据")
        return cached
    
    if not NBA_API_AVAILABLE:
        return get_today_games_local()
    
    try:
        logger.info("从NBA API获取今日比赛...")
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        result = f"🏀 近期NBA比赛\n"
        result += "=" * 50 + "\n"
        
        for game_date in [yesterday, today]:
            try:
                scoreboard = scoreboardv2.ScoreboardV2(game_date=game_date)
                data = scoreboard.get_dict()
                
                headers = data['resultSets'][0]['headers']
                rows = data['resultSets'][0]['rowSet']
                
                if rows:
                    result += f"\n📅 {game_date}\n"
                    result += "-" * 50 + "\n"
                    
                    for row in rows:
                        game_data = dict(zip(headers, row))
                        home_team = game_data.get('HOME_TEAM_NAME', game_data.get('TEAM_NAME', ''))
                        away_team = game_data.get('VISITOR_TEAM_NAME', '')
                        home_score = game_data.get('HOME_TEAM_SCORE', '')
                        away_score = game_data.get('VISITOR_TEAM_SCORE', '')
                        status = game_data.get('GAME_STATUS_TEXT', game_data.get('STATUS', ''))
                        
                        if home_team:
                            result += f"{away_team} vs {home_team}"
                            if home_score and away_score:
                                result += f" | {away_score}-{home_score}"
                            result += f" | {status}\n"
                            
            except Exception as e:
                logger.warning(f"获取{game_date}比赛失败: {e}")
                continue
        
        if "vs" not in result:
            result += "\n暂无近期比赛数据\n"
        
        cache.set(cache_key, result, ttl=300)
        return result
        
    except Exception as e:
        logger.error(f"获取比赛数据失败: {e}")
        return get_today_games_local()


def get_player_stats_live(player_name: str) -> str:
    cache_key = f"player_{player_name}"
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"使用缓存的球员数据: {player_name}")
        return cached
    
    if not NBA_API_AVAILABLE:
        return get_player_info_local(player_name)
    
    try:
        logger.info(f"从NBA API获取球员数据: {player_name}")
        player_id = get_player_id(player_name)
        
        if not player_id:
            return f"未找到球员: {player_name}"
        
        player_info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        info_data = player_info.get_dict()
        
        headers = info_data['resultSets'][0]['headers']
        row = info_data['resultSets'][0]['rowSet'][0] if info_data['resultSets'][0]['rowSet'] else None
        
        if not row:
            return f"未找到球员 {player_name} 的详细信息"
        
        player_data = dict(zip(headers, row))
        
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        career_data = career.get_dict()
        
        season_headers = career_data['resultSets'][0]['headers']
        season_rows = career_data['resultSets'][0]['rowSet']
        
        latest_season = None
        if season_rows:
            latest_season = dict(zip(season_headers, season_rows[-1]))
        
        result = f"👤 {player_data.get('DISPLAY_FIRST_LAST', player_name)}\n"
        result += "=" * 40 + "\n"
        result += f"球队: {player_data.get('TEAM_NAME', '未知')}\n"
        result += f"位置: {player_data.get('POSITION', '未知')}\n"
        result += f"身高: {player_data.get('HEIGHT', '未知')}\n"
        result += f"体重: {player_data.get('WEIGHT', '未知')} lbs\n"
        result += f"球衣号码: #{player_data.get('JERSEY', '未知')}\n"
        result += f"选秀年份: {player_data.get('DRAFT_YEAR', '未知')}\n"
        
        if latest_season:
            result += f"\n📊 {latest_season.get('SEASON_ID', '本赛季')}数据:\n"
            result += "-" * 40 + "\n"
            
            gp = latest_season.get('GP', 0)
            if gp > 0:
                ppg = latest_season.get('PTS', 0) / gp
                rpg = latest_season.get('REB', 0) / gp
                apg = latest_season.get('AST', 0) / gp
                spg = latest_season.get('STL', 0) / gp
                bpg = latest_season.get('BLK', 0) / gp
                
                result += f"场均得分: {ppg:.1f}\n"
                result += f"场均篮板: {rpg:.1f}\n"
                result += f"场均助攻: {apg:.1f}\n"
                result += f"场均抢断: {spg:.1f}\n"
                result += f"场均盖帽: {bpg:.1f}\n"
            else:
                result += "暂无本赛季数据\n"
        
        cache.set(cache_key, result, ttl=3600)
        return result
        
    except Exception as e:
        logger.error(f"获取球员数据失败: {e}")
        return get_player_info_local(player_name)


def get_league_leaders_live(stat_type: str = "PTS", top_n: int = 10) -> str:
    cache_key = f"leaders_{stat_type}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    if not NBA_API_AVAILABLE:
        return "实时数据不可用，请安装 nba_api 库"
    
    try:
        logger.info(f"获取{stat_type}排行榜...")
        
        stat_names = {
            "PTS": "得分榜",
            "REB": "篮板榜",
            "AST": "助攻榜",
            "STL": "抢断榜",
            "BLK": "盖帽榜"
        }
        
        leaders = leagueleaders.LeagueLeaders(stat_category=stat_type)
        data = leaders.get_dict()
        
        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        
        result = f"🏆 NBA {stat_names.get(stat_type, stat_type)} TOP {top_n}\n"
        result += "=" * 50 + "\n"
        
        for i, row in enumerate(rows[:top_n], 1):
            player_data = dict(zip(headers, row))
            name = player_data.get('PLAYER', '未知')
            team = player_data.get('TEAM', '未知')
            value = player_data.get(stat_type, 0)
            
            result += f"{i:2}. {name:20} ({team:4}) - {value:.1f}\n"
        
        cache.set(cache_key, result, ttl=3600)
        return result
        
    except Exception as e:
        logger.error(f"获取排行榜失败: {e}")
        return f"获取{stat_type}排行榜失败，请稍后重试"


def get_team_schedule_live(team_name: str) -> str:
    cache_key = f"schedule_{team_name}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    if not NBA_API_AVAILABLE:
        return get_team_schedule_local(team_name)
    
    try:
        logger.info(f"获取{team_name}赛程...")
        team_id = get_team_id(team_name)
        
        if not team_id:
            return f"未找到球队: {team_name}"
        
        gamelog = teamgamelog.TeamGameLog(team_id=team_id)
        data = gamelog.get_dict()
        
        headers = data['resultSets'][0]['headers']
        rows = data['resultSets'][0]['rowSet']
        
        team_display = TEAM_NAMES.get(team_name.upper(), team_name)
        result = f"📅 {team_display} 近期赛程\n"
        result += "=" * 50 + "\n"
        
        for row in rows[:10]:
            game_data = dict(zip(headers, row))
            date = game_data.get('GAME_DATE', '')
            matchup = game_data.get('MATCHUP', '')
            wl = game_data.get('WL', '')
            pts = game_data.get('PTS', 0)
            opp_pts = game_data.get('OPP_PTS', 0)
            
            result += f"{date} {matchup} | {pts}-{opp_pts} {wl}\n"
        
        cache.set(cache_key, result, ttl=1800)
        return result
        
    except Exception as e:
        logger.error(f"获取赛程失败: {e}")
        return get_team_schedule_local(team_name)


def get_standings_local() -> str:
    from modules.nba_data import get_standings
    return get_standings()


def get_today_games_local() -> str:
    from modules.nba_data import get_today_games
    return get_today_games()


def get_player_info_local(player_name: str) -> str:
    from modules.nba_data import get_player_info
    return get_player_info(player_name)


def get_team_schedule_local(team_name: str) -> str:
    from modules.nba_data import get_team_schedule
    return get_team_schedule(team_name)


# 导入新的数据提供者
try:
    from modules.data_provider import data_provider
    DATA_PROVIDER_AVAILABLE = True
except ImportError:
    DATA_PROVIDER_AVAILABLE = False


def get_standings() -> str:
    # 优先使用新的数据提供者
    if DATA_PROVIDER_AVAILABLE and config.USE_LIVE_DATA:
        result = data_provider.get_standings()
        if result and "失败" not in result:
            return result
    # 回退到原有方法
    if config.USE_LIVE_DATA and NBA_API_AVAILABLE:
        return get_standings_live()
    return get_standings_local()


def get_today_games() -> str:
    # 优先使用新的数据提供者
    if DATA_PROVIDER_AVAILABLE and config.USE_LIVE_DATA:
        result = data_provider.get_today_games()
        if result and "失败" not in result and "暂无" not in result:
            return result
    # 回退到原有方法
    if config.USE_LIVE_DATA and NBA_API_AVAILABLE:
        return get_today_games_live()
    return get_today_games_local()


def get_player_info(player_name: str) -> str:
    # 优先使用新的数据提供者
    if DATA_PROVIDER_AVAILABLE and config.USE_LIVE_DATA:
        result = data_provider.get_player_info(player_name)
        if result and "未找到" not in result:
            return result
    # 回退到原有方法
    if config.USE_LIVE_DATA and NBA_API_AVAILABLE:
        return get_player_stats_live(player_name)
    return get_player_info_local(player_name)


def get_team_schedule(team_name: str) -> str:
    if config.USE_LIVE_DATA and NBA_API_AVAILABLE:
        return get_team_schedule_live(team_name)
    return get_team_schedule_local(team_name)


def get_league_leaders(stat_type: str = "PTS", top_n: int = 10) -> str:
    if config.USE_LIVE_DATA and NBA_API_AVAILABLE:
        return get_league_leaders_live(stat_type, top_n)
    return "实时排行榜数据不可用，请安装 nba_api 库"


def compare_players(player1: str, player2: str) -> str:
    if not NBA_API_AVAILABLE:
        return f"无法对比{player1}和{player2}，请安装 nba_api 库获取实时数据"
    
    try:
        stats1 = get_player_stats_live(player1)
        stats2 = get_player_stats_live(player2)
        
        result = f"📊 球员对比: {player1} vs {player2}\n"
        result += "=" * 50 + "\n\n"
        result += f"【{player1}】\n{stats1}\n\n"
        result += f"【{player2}】\n{stats2}\n"
        
        return result
    except Exception as e:
        logger.error(f"球员对比失败: {e}")
        return f"对比失败: {str(e)}"


if __name__ == "__main__":
    print("=" * 50)
    print("NBA 实时数据模块测试")
    print("=" * 50)
    
    print("\n1. 测试排名:")
    print(get_standings()[:500])
    
    print("\n2. 测试球员数据:")
    print(get_player_info("詹姆斯")[:500])
    
    print("\n3. 测试排行榜:")
    print(get_league_leaders("PTS", 5))
