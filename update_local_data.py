"""
NBA本地数据更新脚本
从免费API获取最新数据并更新到本地数据库
"""

import sys
import os
import requests
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.local_database import get_connection, init_database

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ==================== 中文名称映射 ====================
# 球员英文名 -> 中文名映射
PLAYER_NAME_CN = {
    "LeBron James": "詹姆斯",
    "Stephen Curry": "库里",
    "Kevin Durant": "杜兰特",
    "Giannis Antetokounmpo": "字母哥",
    "Nikola Jokic": "约基奇",
    "Luka Doncic": "东契奇",
    "Anthony Davis": "浓眉",
    "James Harden": "哈登",
    "Russell Westbrook": "威少",
    "Kawhi Leonard": "伦纳德",
    "Jayson Tatum": "塔图姆",
    "Jaylen Brown": "布朗",
    "Joel Embiid": "恩比德",
    "Devin Booker": "布克",
    "Damian Lillard": "利拉德",
    "Ja Morant": "莫兰特",
    "Anthony Edwards": "爱德华兹",
    "Shai Gilgeous-Alexander": "亚历山大",
    "Paul George": "乔治",
    "Jimmy Butler": "巴特勒",
    "Kyrie Irving": "欧文",
    "Chris Paul": "保罗",
    "Zion Williamson": "锡安",
    "De'Aaron Fox": "福克斯",
    "Bradley Beal": "比尔",
    "Zach LaVine": "拉文",
    "DeMar DeRozan": "德罗赞",
    "D'Angelo Russell": "拉塞尔",
    "Victor Wembanyama": "文班亚马",
    "Tyrese Haliburton": "哈利伯顿",
    "Domantas Sabonis": "萨博尼斯",
    "Trae Young": "特雷杨",
    "Donovan Mitchell": "米切尔",
    "Karl-Anthony Towns": "唐斯",
    "Ben Simmons": "西蒙斯",
    "Brandon Ingram": "英格拉姆",
    "Bam Adebayo": "阿德巴约",
    "Rudy Gobert": "戈贝尔",
    "Klay Thompson": "汤普森",
    "Draymond Green": "追梦格林",
}

# 球队缩写 -> 中文名映射
TEAM_NAME_CN = {
    "ATL": "亚特兰大老鹰",
    "BOS": "波士顿凯尔特人",
    "BKN": "布鲁克林篮网",
    "CHA": "夏洛特黄蜂",
    "CHI": "芝加哥公牛",
    "CLE": "克利夫兰骑士",
    "DAL": "达拉斯独行侠",
    "DEN": "丹佛掘金",
    "DET": "底特律活塞",
    "GSW": "金州勇士",
    "HOU": "休斯顿火箭",
    "IND": "印第安纳步行者",
    "LAC": "洛杉矶快船",
    "LAL": "洛杉矶湖人",
    "MEM": "孟菲斯灰熊",
    "MIA": "迈阿密热火",
    "MIL": "密尔沃基雄鹿",
    "MIN": "明尼苏达森林狼",
    "NOP": "新奥尔良鹈鹕",
    "NYK": "纽约尼克斯",
    "OKC": "俄克拉荷马雷霆",
    "ORL": "奥兰多魔术",
    "PHI": "费城76人",
    "PHX": "菲尼克斯太阳",
    "POR": "波特兰开拓者",
    "SAC": "萨克拉门托国王",
    "SAS": "圣安东尼奥马刺",
    "TOR": "多伦多猛龙",
    "UTA": "犹他爵士",
    "WAS": "华盛顿奇才",
}


class NBADataUpdater:
    """NBA数据更新器"""

    def __init__(self):
        self.conn = get_connection()
        self.cursor = self.conn.cursor()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        })

    def update_all(self):
        """更新所有数据"""
        logger.info("开始更新NBA数据...")
        
        logger.info("1. 更新球员数据...")
        self.update_players_from_espn()
        
        logger.info("2. 更新赛季统计数据...")
        self.update_season_stats_from_espn()
        
        logger.info("3. 更新排名数据...")
        self.update_standings_from_espn()
        
        logger.info("4. 更新最新冠军...")
        self.update_latest_champion()
        
        logger.info("5. 更新最新MVP...")
        self.update_latest_mvp()
        
        self.conn.commit()
        logger.info("数据更新完成")

    # ==================== 球员数据更新 ====================

    def update_players_from_espn(self):
        """从ESPN更新球员信息"""
        logger.info("从ESPN获取球员数据...")
        
        try:
            teams = self._get_espn_teams()
            if not teams:
                logger.warning("无法获取球队列表")
                return

            for team_data in teams[:30]:
                team_info = team_data.get('team', {})
                team_id = team_info.get('id')
                team_abbr = team_info.get('abbreviation', '')
                if not team_id:
                    continue
                    
                players = self._get_espn_team_roster(team_id)
                if players:
                    self._update_players(players, team_abbr)
                    
        except Exception as e:
            logger.error(f"更新球员数据失败: {e}")

    def _get_espn_teams(self):
        """获取ESPN球队列表"""
        try:
            url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams'
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                sports = data.get('sports', [])
                if sports:
                    leagues = sports[0].get('leagues', [])
                    if leagues:
                        return leagues[0].get('teams', [])
        except Exception as e:
            logger.error(f"获取ESPN球队失败: {e}")
        return []

    def _get_espn_team_roster(self, team_id):
        """获取ESPN球队阵容"""
        try:
            url = f'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}/roster'
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return data.get('athletes', [])
        except Exception as e:
            logger.error(f"获取球队阵容失败: {e}")
        return []

    def _update_players(self, players, team_abbr):
        """更新球员到数据库"""
        for player in players:
            try:
                name_en = player.get('displayName', '')
                if not name_en:
                    continue
                
                # 获取中文名
                name_cn = PLAYER_NAME_CN.get(name_en, name_en)
                
                # 检查是否已存在
                self.cursor.execute("SELECT id FROM players WHERE name_en = ?", (name_en,))
                existing = self.cursor.fetchone()
                
                if not existing:
                    # 解析位置
                    position = player.get('position', {}).get('name', '')
                    position_cn = self._translate_position(position)
                    
                    # 解析身高体重 (ESPN: 英寸/磅 -> cm/kg)
                    height_inches = player.get('height', 0)
                    weight_lbs = player.get('weight', 0)
                    height_cm = int(height_inches * 2.54) if height_inches else 0
                    weight_kg = int(weight_lbs * 0.453592) if weight_lbs else 0
                    
                    # 解析生日
                    birth_date = player.get('dateOfBirth', '')
                    if birth_date:
                        birth_date = birth_date.split('T')[0]  # 去掉时间部分
                    
                    # 解析大学
                    school = ''
                    college = player.get('college', {})
                    if college:
                        school = college.get('name', '')
                    
                    # 解析球衣号码
                    jersey = player.get('jersey', '')
                    
                    # 解析经验
                    experience = player.get('experience', {}).get('years', 0)
                    
                    self.cursor.execute("""
                        INSERT INTO players (name_cn, name_en, team_abbr, position, jersey_number, height_cm, weight_kg, country, birth_date, draft_year, school, aliases, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (name_cn, name_en, team_abbr, position_cn, jersey, height_cm, weight_kg, '', birth_date, 0, school, name_en, f"{name_cn}，{team_abbr}队球员"))
                    
                    logger.info(f"添加球员: {name_cn} ({name_en}) - {position_cn}, {height_cm}cm, {weight_kg}kg")
                else:
                    # 更新球队信息
                    self.cursor.execute("""
                        UPDATE players SET team_abbr = ? WHERE name_en = ?
                    """, (team_abbr, name_en))
                    
            except Exception as e:
                logger.error(f"更新球员 {player.get('displayName', 'N/A')} 失败: {e}")

    def _translate_position(self, position):
        """翻译位置为中文"""
        pos_map = {
            'PG': '控球后卫',
            'SG': '得分后卫',
            'SF': '小前锋',
            'PF': '大前锋',
            'C': '中锋',
            'Guard': '后卫',
            'Forward': '前锋',
            'Center': '中锋',
        }
        return pos_map.get(position, position)

    # ==================== 赛季统计更新 ====================

    def update_season_stats_from_espn(self):
        """从ESPN更新赛季统计数据"""
        logger.info("从ESPN获取赛季统计数据...")
        
        try:
            # 获取赛季领袖
            leaders = self._get_espn_season_leaders()
            if leaders:
                self._update_season_stats(leaders)
        except Exception as e:
            logger.error(f"更新赛季统计失败: {e}")

    def _get_espn_season_leaders(self):
        """获取ESPN赛季领袖"""
        try:
            url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/season/leaders'
            r = self.session.get(url, timeout=10, params={'season': '2025', 'seasontype': '2'})
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.error(f"获取赛季领袖失败: {e}")
        return None

    def _update_season_stats(self, data):
        """更新赛季统计"""
        # 解析并更新赛季统计数据
        pass

    # ==================== 排名更新 ====================

    def update_standings_from_espn(self):
        """从ESPN更新排名数据"""
        logger.info("从ESPN获取排名数据...")
        
        try:
            standings = self._get_espn_standings()
            if standings:
                self._update_standings(standings)
        except Exception as e:
            logger.error(f"更新排名失败: {e}")

    def _get_espn_standings(self):
        """获取ESPN排名"""
        try:
            url = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/standings'
            r = self.session.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logger.error(f"获取排名失败: {e}")
        return None

    def _update_standings(self, data):
        """更新排名"""
        # 解析并更新排名数据
        pass

    # ==================== 冠军更新 ====================

    def update_latest_champion(self):
        """更新最新冠军信息"""
        logger.info("更新最新冠军...")
        # 冠军数据通常是历史数据，不需要频繁更新
        # 可以在新赛季结束后手动更新

    # ==================== MVP更新 ====================

    def update_latest_mvp(self):
        """更新最新MVP信息"""
        logger.info("更新最新MVP...")
        # MVP数据通常在赛季结束后更新
        # 可以在赛季结束后手动更新

    def close(self):
        """关闭连接"""
        self.conn.close()


def main():
    """主函数"""
    # 初始化数据库
    init_database()
    
    # 创建更新器
    updater = NBADataUpdater()
    
    try:
        updater.update_all()
    finally:
        updater.close()


if __name__ == "__main__":
    main()
