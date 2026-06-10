#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import logging
from typing import Optional, List, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'nba_local.db')


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name_cn TEXT NOT NULL,
        name_en TEXT NOT NULL,
        team_abbr TEXT,
        position TEXT,
        jersey_number TEXT,
        height_cm INTEGER,
        weight_kg INTEGER,
        country TEXT,
        birth_date TEXT,
        draft_year INTEGER,
        draft_round INTEGER,
        draft_number INTEGER,
        school TEXT,
        aliases TEXT,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS career_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        seasons INTEGER,
        games_played INTEGER,
        total_points INTEGER,
        total_rebounds INTEGER,
        total_assists INTEGER,
        total_steals INTEGER,
        total_blocks INTEGER,
        ppg REAL,
        rpg REAL,
        apg REAL,
        spg REAL,
        bpg REAL,
        fg_pct REAL,
        three_pct REAL,
        ft_pct REAL,
        mpg REAL,
        FOREIGN KEY (player_id) REFERENCES players(id)
    );

    CREATE TABLE IF NOT EXISTS season_stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER NOT NULL,
        season TEXT NOT NULL,
        team_abbr TEXT,
        games INTEGER,
        ppg REAL,
        rpg REAL,
        apg REAL,
        spg REAL,
        bpg REAL,
        fg_pct REAL,
        three_pct REAL,
        ft_pct REAL,
        mpg REAL,
        FOREIGN KEY (player_id) REFERENCES players(id)
    );

    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        abbr TEXT UNIQUE NOT NULL,
        name_cn TEXT NOT NULL,
        name_en TEXT NOT NULL,
        city TEXT,
        conference TEXT,
        division TEXT,
        founded_year INTEGER,
        championships INTEGER,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS champions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        champion TEXT NOT NULL,
        runner_up TEXT,
        mvp TEXT,
        finals_mvp TEXT,
        score TEXT
    );

    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        record_type TEXT NOT NULL,
        holder TEXT NOT NULL,
        value TEXT NOT NULL,
        season TEXT,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS mvp_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL,
        player TEXT NOT NULL,
        team TEXT,
        award_type TEXT
    );

    CREATE TABLE IF NOT EXISTS faq (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_pattern TEXT NOT NULL,
        answer TEXT NOT NULL,
        category TEXT
    );
    """)

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM players")
    if cursor.fetchone()[0] == 0:
        _seed_players(cursor)
    cursor.execute("SELECT COUNT(*) FROM teams")
    if cursor.fetchone()[0] == 0:
        _seed_teams(cursor)
    cursor.execute("SELECT COUNT(*) FROM champions")
    if cursor.fetchone()[0] == 0:
        _seed_champions(cursor)
    cursor.execute("SELECT COUNT(*) FROM records")
    if cursor.fetchone()[0] == 0:
        _seed_records(cursor)
    cursor.execute("SELECT COUNT(*) FROM mvp_history")
    if cursor.fetchone()[0] == 0:
        _seed_mvp(cursor)
    cursor.execute("SELECT COUNT(*) FROM faq")
    if cursor.fetchone()[0] == 0:
        _seed_faq(cursor)
    cursor.execute("SELECT COUNT(*) FROM career_stats")
    if cursor.fetchone()[0] == 0:
        _seed_career_stats(cursor)
    cursor.execute("SELECT COUNT(*) FROM season_stats")
    if cursor.fetchone()[0] == 0:
        _seed_season_stats(cursor)

    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")


def _seed_players(c):
    players = [
        ("詹姆斯", "LeBron James", "LAL", "小前锋", "23", 206, 113, "美国", "1984-12-30", 2003, 1, 1, "圣文森特-圣玛丽高中", "老詹,詹皇,小皇帝,King James", "4届NBA总冠军，4届MVP，NBA历史得分王，被广泛认为是篮球历史上最伟大的球员之一"),
        ("库里", "Stephen Curry", "GSW", "控球后卫", "30", 188, 84, "美国", "1988-03-14", 2009, 1, 7, "戴维森学院", "萌神,小学生,Chef Curry,咖喱", "4届NBA总冠军，2届MVP，NBA历史三分王，改变了现代篮球的打法"),
        ("杜兰特", "Kevin Durant", "PHX", "小前锋", "35", 208, 109, "美国", "1988-09-29", 2007, 1, 2, "德克萨斯大学", "KD,死神,书包杜", "2届NBA总冠军，2届FMVP，4届得分王，历史顶级得分手"),
        ("字母哥", "Giannis Antetokounmpo", "MIL", "大前锋", "34", 211, 110, "希腊", "1994-12-06", 2013, 1, 15, "希腊联赛", "希腊怪兽,Greek Freak", "2届MVP，1届总冠军，1届FMVP，身体素质惊人"),
        ("约基奇", "Nikola Jokic", "DEN", "中锋", "15", 208, 113, "塞尔维亚", "1995-02-19", 2014, 2, 41, "塞尔维亚联赛", "约老师,小丑,Joker", "3届MVP，1届总冠军，1届FMVP，历史级传球中锋"),
        ("东契奇", "Luka Doncic", "LAL", "控球后卫", "77", 201, 104, "斯洛文尼亚", "1999-02-28", 2018, 1, 3, "皇家马德里", "077,卢卡,Luka Magic", "NBA顶级球星，多次入选全明星，全面的技术能力"),
        ("浓眉", "Anthony Davis", "LAL", "大前锋", "3", 208, 106, "美国", "1993-03-11", 2012, 1, 1, "肯塔基大学", "AD,眉子", "1届NBA总冠军，顶级防守者，攻防兼备"),
        ("哈登", "James Harden", "LAC", "得分后卫", "1", 196, 100, "美国", "1989-08-26", 2009, 1, 3, "亚利桑那州立大学", "登哥,大胡子", "1届MVP，3届得分王，顶级后卫"),
        ("威少", "Russell Westbrook", "DEN", "控球后卫", "0", 191, 91, "美国", "1988-11-12", 2008, 1, 4, "UCLA", "神龟,Westbrook", "1届MVP，NBA历史三双王，爆发力惊人"),
        ("伦纳德", "Kawhi Leonard", "LAC", "小前锋", "2", 201, 102, "美国", "1991-06-29", 2011, 1, 15, "圣地亚哥州立大学", "小卡,卡哇伊,The Klaw", "2届NBA总冠军，2届FMVP，2届DPOY，攻防一体"),
        ("塔图姆", "Jayson Tatum", "BOS", "小前锋", "0", 203, 95, "美国", "1998-03-03", 2017, 1, 3, "杜克大学", "獭兔", "1届NBA总冠军，多次入选全明星，凯尔特人当家球星"),
        ("布朗", "Jaylen Brown", "BOS", "得分后卫", "7", 198, 101, "美国", "1996-10-24", 2016, 1, 3, "加州大学伯克利分校", "杰伦", "1届NBA总冠军，1届FMVP，攻防兼备"),
        ("恩比德", "Joel Embiid", "PHI", "中锋", "21", 213, 127, "喀麦隆", "1994-03-16", 2014, 1, 3, "堪萨斯大学", "大帝,过程,The Process", "1届MVP，1届得分王，统治级中锋"),
        ("布克", "Devin Booker", "PHX", "得分后卫", "1", 196, 93, "美国", "1996-10-30", 2015, 1, 13, "肯塔基大学", "Book", "太阳当家球星，顶级得分手，单场70分"),
        ("利拉德", "Damian Lillard", "MIL", "控球后卫", "0", 188, 88, "美国", "1990-07-15", 2012, 1, 6, "韦伯州立大学", "利指导,表哥,Dame", "顶级控卫，关键球能力出色，多次绝杀"),
        ("莫兰特", "Ja Morant", "MEM", "控球后卫", "12", 191, 79, "美国", "1999-08-10", 2019, 1, 2, "莫瑞州立大学", "", "灰熊当家球星，爆发力惊人，顶级控卫"),
        ("爱德华兹", "Anthony Edwards", "MIN", "得分后卫", "5", 193, 102, "美国", "2001-08-05", 2020, 1, 1, "佐治亚大学", "华子,蚁人,Ant-Man", "森林狼当家球星，新一代球星代表"),
        ("亚历山大", "Shai Gilgeous-Alexander", "OKC", "控球后卫", "2", 198, 88, "加拿大", "1998-07-12", 2018, 1, 11, "肯塔基大学", "SGA,鸭梨", "雷霆当家球星，1届MVP，顶级得分手"),
        ("乔治", "Paul George", "PHI", "小前锋", "8", 203, 99, "美国", "1990-05-02", 2010, 1, 10, "弗雷斯诺州立大学", "泡椒,PG13", "多次入选全明星，攻防兼备"),
        ("巴特勒", "Jimmy Butler", "MIA", "小前锋", "22", 201, 95, "美国", "1989-09-14", 2011, 1, 30, "马奎特大学", "JB,吉米", "热火当家球星，季后赛表现突出"),
        ("欧文", "Kyrie Irving", "DAL", "控球后卫", "11", 188, 88, "美国", "1992-03-23", 2011, 1, 1, "杜克大学", "德鲁大叔,Uncle Drew", "1届NBA总冠军，顶级控球技术，关键球大师"),
        ("保罗", "Chris Paul", "SAS", "控球后卫", "3", 183, 79, "美国", "1985-05-06", 2005, 1, 4, "维克森林大学", "CP3,炮哥", "历史级控卫，5届助攻王，6届抢断王"),
        ("锡安", "Zion Williamson", "NOP", "大前锋", "1", 198, 128, "美国", "2000-07-06", 2019, 1, 1, "杜克大学", "胖虎", "身体素质惊人，内线统治力"),
        ("福克斯", "De'Aaron Fox", "SAC", "控球后卫", "5", 191, 84, "美国", "1997-12-20", 2017, 1, 5, "肯塔基大学", "", "国王当家控卫，速度极快"),
        ("比尔", "Bradley Beal", "PHX", "得分后卫", "3", 193, 93, "美国", "1993-06-28", 2012, 1, 3, "佛罗里达大学", "", "顶级得分手，多次场均30+"),
        ("拉文", "Zach LaVine", "CHI", "得分后卫", "8", 196, 91, "美国", "1995-03-10", 2014, 1, 13, "UCLA", "", "两届扣篮大赛冠军，顶级得分手"),
        ("德罗赞", "DeMar DeRozan", "SAC", "小前锋", "11", 198, 100, "美国", "1989-08-07", 2009, 1, 9, "USC", "", "中距离大师，多次入选全明星"),
        ("拉塞尔", "D'Angelo Russell", "LAL", "控球后卫", "1", 193, 88, "美国", "1996-02-23", 2015, 1, 2, "俄亥俄州立大学", "D-Lo", "湖人后卫，曾入选全明星"),
        ("文班亚马", "Victor Wembanyama", "SAS", "中锋", "1", 224, 95, "法国", "2004-01-04", 2023, 1, 1, "法国联赛", "斑马,Wemby", "2023年状元，天赋异禀，新一代超级巨星"),
        ("哈利伯顿", "Tyrese Haliburton", "IND", "控球后卫", "0", 196, 84, "美国", "2000-02-29", 2020, 1, 12, "爱荷华州立大学", "", "步行者当家控卫，顶级组织者"),
        ("萨博尼斯", "Domantas Sabonis", "SAC", "中锋", "11", 208, 109, "立陶宛", "1996-03-03", 2016, 1, 11, "冈萨加大学", "小萨", "国王核心，顶级篮板手和传球手"),
        ("特雷杨", "Trae Young", "ATL", "控球后卫", "11", 185, 82, "美国", "1998-09-19", 2018, 1, 5, "俄克拉荷马大学", "吹杨", "老鹰当家球星，远投和传球出色"),
        ("米切尔", "Donovan Mitchell", "CLE", "得分后卫", "45", 185, 97, "美国", "1996-09-07", 2017, 1, 13, "路易斯维尔大学", "蜘蛛侠,Spida", "骑士当家球星，顶级得分手"),
        ("唐斯", "Karl-Anthony Towns", "NYK", "中锋", "32", 211, 112, "美国", "1995-11-15", 2015, 1, 1, "肯塔基大学", "KAT,唐先生", "1届最佳新秀，顶级空间型中锋"),
        ("西蒙斯", "Ben Simmons", "LAC", "控球后卫", "10", 208, 104, "澳大利亚", "1996-07-20", 2016, 1, 1, "LSU", "", "1届最佳新秀，顶级防守和组织"),
        ("英格拉姆", "Brandon Ingram", "TOR", "小前锋", "14", 201, 86, "美国", "1997-09-02", 2016, 1, 2, "杜克大学", "", "1届最佳进步球员，技术全面"),
        ("阿德巴约", "Bam Adebayo", "MIA", "中锋", "13", 206, 116, "美国", "1997-07-18", 2017, 1, 14, "肯塔基大学", "", "热火核心，顶级防守者"),
        ("戈贝尔", "Rudy Gobert", "MIN", "中锋", "27", 216, 117, "法国", "1992-06-26", 2013, 1, 27, "法国联赛", "法国铁塔", "4届DPOY，顶级护框者"),
        ("汤普森", "Klay Thompson", "DAL", "得分后卫", "31", 198, 99, "美国", "1990-02-08", 2011, 1, 11, "华盛顿州立大学", "佛祖,Klay", "4届NBA总冠军，顶级3D球员，单节37分纪录"),
        ("追梦格林", "Draymond Green", "GSW", "大前锋", "23", 198, 104, "美国", "1990-03-04", 2012, 1, 35, "密歇根州立大学", "追梦,Draymond", "4届NBA总冠军，1届DPOY，勇士防守核心"),
    ]
    c.executemany("""INSERT INTO players 
        (name_cn, name_en, team_abbr, position, jersey_number, height_cm, weight_kg, country, birth_date, draft_year, draft_round, draft_number, school, aliases, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", players)


def _seed_teams(c):
    teams = [
        ("ATL", "亚特兰大老鹰", "Atlanta Hawks", "亚特兰大", "东部", "东南", 1949, 1, "老鹰队历史悠久，曾于1958年夺得总冠军"),
        ("BOS", "波士顿凯尔特人", "Boston Celtics", "波士顿", "东部", "大西洋", 1946, 18, "NBA最成功的球队之一，18次总冠军，与湖人并列历史第一"),
        ("BKN", "布鲁克林篮网", "Brooklyn Nets", "布鲁克林", "东部", "大西洋", 1967, 0, "篮网队位于纽约布鲁克林，尚未获得总冠军"),
        ("CHA", "夏洛特黄蜂", "Charlotte Hornets", "夏洛特", "东部", "东南", 1988, 0, "黄蜂队由迈克尔·乔丹拥有"),
        ("CHI", "芝加哥公牛", "Chicago Bulls", "芝加哥", "东部", "中部", 1966, 6, "乔丹时代6次总冠军，两次三连冠伟业"),
        ("CLE", "克利夫兰骑士", "Cleveland Cavaliers", "克利夫兰", "东部", "中部", 1970, 1, "2016年詹姆斯带领骑士逆转夺冠"),
        ("DAL", "达拉斯独行侠", "Dallas Mavericks", "达拉斯", "西部", "西南", 1980, 1, "2011年诺维茨基带领球队夺冠"),
        ("DEN", "丹佛掘金", "Denver Nuggets", "丹佛", "西部", "西北", 1967, 1, "2023年约基奇带领球队首夺总冠军"),
        ("DET", "底特律活塞", "Detroit Pistons", "底特律", "东部", "中部", 1941, 3, "坏孩子军团时代2连冠，2004年再夺一冠"),
        ("GSW", "金州勇士", "Golden State Warriors", "旧金山", "西部", "太平洋", 1946, 7, "库里时代4次总冠军，改变了现代篮球打法"),
        ("HOU", "休斯顿火箭", "Houston Rockets", "休斯顿", "西部", "西南", 1967, 2, "奥拉朱旺时代2连冠，姚明曾效力"),
        ("IND", "印第安纳步行者", "Indiana Pacers", "印第安纳", "东部", "中部", 1967, 0, "雷吉·米勒时代标志性球队"),
        ("LAC", "洛杉矶快船", "Los Angeles Clippers", "洛杉矶", "西部", "太平洋", 1970, 0, "尚未获得总冠军"),
        ("LAL", "洛杉矶湖人", "Los Angeles Lakers", "洛杉矶", "西部", "太平洋", 1947, 17, "NBA最伟大的球队之一，17次总冠军，科比、魔术师、詹姆斯等传奇"),
        ("MEM", "孟菲斯灰熊", "Memphis Grizzlies", "孟菲斯", "西部", "西南", 1995, 0, "尚未获得总冠军，以强硬防守著称"),
        ("MIA", "迈阿密热火", "Miami Heat", "迈阿密", "东部", "东南", 1988, 3, "韦德时代3次总冠军，詹姆斯曾效力2年夺2冠"),
        ("MIL", "密尔沃基雄鹿", "Milwaukee Bucks", "密尔沃基", "东部", "中部", 1968, 2, "贾巴尔时代1冠，字母哥时代2021年夺冠"),
        ("MIN", "明尼苏达森林狼", "Minnesota Timberwolves", "明尼苏达", "西部", "西北", 1989, 0, "加内特时代标志性球队"),
        ("NOP", "新奥尔良鹈鹕", "New Orleans Pelicans", "新奥尔良", "西部", "西南", 2002, 0, "尚未获得总冠军"),
        ("NYK", "纽约尼克斯", "New York Knicks", "纽约", "东部", "大西洋", 1946, 2, "NBA最值钱的球队之一，2次总冠军"),
        ("OKC", "俄克拉荷马雷霆", "Oklahoma City Thunder", "俄克拉荷马", "西部", "西北", 1967, 1, "杜兰特和威少时代标志性球队，2025年亚历山大MVP赛季"),
        ("ORL", "奥兰多魔术", "Orlando Magic", "奥兰多", "东部", "东南", 1989, 0, "奥尼尔和霍华德曾效力"),
        ("PHI", "费城76人", "Philadelphia 76ers", "费城", "东部", "大西洋", 1946, 3, "张伯伦和艾弗森曾效力，3次总冠军"),
        ("PHX", "菲尼克斯太阳", "Phoenix Suns", "菲尼克斯", "西部", "太平洋", 1968, 0, "纳什时代跑轰战术标志性球队"),
        ("POR", "波特兰开拓者", "Portland Trail Blazers", "波特兰", "西部", "西北", 1970, 1, "1977年比尔·沃顿带队夺冠"),
        ("SAC", "萨克拉门托国王", "Sacramento Kings", "萨克拉门托", "西部", "太平洋", 1945, 1, "1951年夺冠后至今未再夺冠"),
        ("SAS", "圣安东尼奥马刺", "San Antonio Spurs", "圣安东尼奥", "西部", "西南", 1967, 5, "邓肯时代5次总冠军，波波维奇执教"),
        ("TOR", "多伦多猛龙", "Toronto Raptors", "多伦多", "东部", "大西洋", 1995, 1, "2019年伦纳德带队夺冠，美国境外首冠"),
        ("UTA", "犹他爵士", "Utah Jazz", "盐湖城", "西部", "西北", 1974, 0, "斯托克顿和马龙时代标志性球队"),
        ("WAS", "华盛顿奇才", "Washington Wizards", "华盛顿", "东部", "东南", 1961, 1, "1978年夺冠，乔丹曾效力"),
    ]
    c.executemany("""INSERT INTO teams 
        (abbr, name_cn, name_en, city, conference, division, founded_year, championships, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", teams)


def _seed_champions(c):
    champions = [
        (2026, "波士顿凯尔特人", "俄克拉荷马雷霆", "尼古拉·约基奇", "杰森·塔图姆", "4-2"),
        (2025, "俄克拉荷马雷霆", "印第安纳步行者", "谢伊·吉尔杰斯-亚历山大", "谢伊·吉尔杰斯-亚历山大", "4-3"),
        (2024, "波士顿凯尔特人", "达拉斯独行侠", "尼古拉·约基奇", "杰伦·布朗", "4-1"),
        (2023, "丹佛掘金", "迈阿密热火", "乔尔·恩比德", "尼古拉·约基奇", "4-1"),
        (2022, "金州勇士", "波士顿凯尔特人", "尼古拉·约基奇", "斯蒂芬·库里", "4-2"),
        (2021, "密尔沃基雄鹿", "菲尼克斯太阳", "尼古拉·约基奇", "扬尼斯·阿德托昆博", "4-2"),
        (2020, "洛杉矶湖人", "迈阿密热火", "扬尼斯·阿德托昆博", "勒布朗·詹姆斯", "4-2"),
        (2019, "多伦多猛龙", "金州勇士", "扬尼斯·阿德托昆博", "科怀·伦纳德", "4-2"),
        (2018, "金州勇士", "克利夫兰骑士", "詹姆斯·哈登", "凯文·杜兰特", "4-0"),
        (2017, "金州勇士", "克利夫兰骑士", "拉塞尔·威斯布鲁克", "凯文·杜兰特", "4-1"),
        (2016, "克利夫兰骑士", "金州勇士", "斯蒂芬·库里", "勒布朗·詹姆斯", "4-3"),
        (2015, "金州勇士", "克利夫兰骑士", "斯蒂芬·库里", "安德烈·伊戈达拉", "4-2"),
        (2014, "圣安东尼奥马刺", "迈阿密热火", "凯文·杜兰特", "科怀·伦纳德", "4-1"),
        (2013, "迈阿密热火", "圣安东尼奥马刺", "勒布朗·詹姆斯", "勒布朗·詹姆斯", "4-3"),
        (2012, "迈阿密热火", "俄克拉荷马雷霆", "勒布朗·詹姆斯", "勒布朗·詹姆斯", "4-1"),
        (2011, "达拉斯独行侠", "迈阿密热火", "德里克·罗斯", "德克·诺维茨基", "4-2"),
        (2010, "洛杉矶湖人", "波士顿凯尔特人", "勒布朗·詹姆斯", "科比·布莱恩特", "4-3"),
        (2009, "洛杉矶湖人", "奥兰多魔术", "勒布朗·詹姆斯", "科比·布莱恩特", "4-1"),
        (2008, "波士顿凯尔特人", "洛杉矶湖人", "科比·布莱恩特", "保罗·皮尔斯", "4-2"),
        (2007, "圣安东尼奥马刺", "克利夫兰骑士", "德克·诺维茨基", "托尼·帕克", "4-0"),
        (2006, "迈阿密热火", "达拉斯独行侠", "史蒂夫·纳什", "德韦恩·韦德", "4-2"),
        (2005, "圣安东尼奥马刺", "底特律活塞", "史蒂夫·纳什", "蒂姆·邓肯", "4-3"),
        (2004, "底特律活塞", "洛杉矶湖人", "凯文·加内特", "昌西·比卢普斯", "4-1"),
        (2003, "圣安东尼奥马刺", "新泽西篮网", "蒂姆·邓肯", "蒂姆·邓肯", "4-2"),
        (2002, "洛杉矶湖人", "新泽西篮网", "蒂姆·邓肯", "沙奎尔·奥尼尔", "4-0"),
        (2001, "洛杉矶湖人", "费城76人", "阿伦·艾弗森", "沙奎尔·奥尼尔", "4-1"),
        (2000, "洛杉矶湖人", "印第安纳步行者", "沙奎尔·奥尼尔", "沙奎尔·奥尼尔", "4-2"),
        (1999, "圣安东尼奥马刺", "纽约尼克斯", "卡尔·马龙", "蒂姆·邓肯", "4-1"),
        (1998, "芝加哥公牛", "犹他爵士", "迈克尔·乔丹", "迈克尔·乔丹", "4-2"),
        (1997, "芝加哥公牛", "犹他爵士", "卡尔·马龙", "迈克尔·乔丹", "4-2"),
        (1996, "芝加哥公牛", "西雅图超音速", "迈克尔·乔丹", "迈克尔·乔丹", "4-2"),
    ]
    c.executemany("INSERT INTO champions (year, champion, runner_up, mvp, finals_mvp, score) VALUES (?, ?, ?, ?, ?, ?)", champions)


def _seed_records(c):
    records = [
        ("得分", "生涯总得分", "勒布朗·詹姆斯", "42,184分", "2003-2025", "NBA历史得分王，超越贾巴尔"),
        ("得分", "单场最高得分", "威尔特·张伯伦", "100分", "1962年", "NBA单场得分纪录，几乎不可能被打破"),
        ("得分", "单赛季场均最高", "威尔特·张伯伦", "50.4分", "1961-62赛季", "单赛季场均得分纪录"),
        ("得分", "三分命中总数", "斯蒂芬·库里", "3,747+", "2009-至今", "NBA历史三分王，改变了篮球打法"),
        ("得分", "单赛季三分命中", "斯蒂芬·库里", "402个", "2015-16赛季", "单赛季三分命中纪录"),
        ("篮板", "生涯总篮板", "威尔特·张伯伦", "23,924个", "1959-1973", "NBA历史篮板王"),
        ("篮板", "单场最高篮板", "威尔特·张伯伦", "55个", "1960年", "NBA单场篮板纪录"),
        ("助攻", "生涯总助攻", "约翰·斯托克顿", "15,806次", "1984-2003", "NBA历史助攻王，纪录几乎不可能被打破"),
        ("助攻", "单赛季总助攻", "约翰·斯托克顿", "1,164次", "1990-91赛季", "单赛季助攻纪录"),
        ("抢断", "生涯总抢断", "约翰·斯托克顿", "3,265次", "1984-2003", "NBA历史抢断王"),
        ("盖帽", "生涯总盖帽", "哈基姆·奥拉朱旺", "3,830次", "1984-2002", "NBA历史盖帽王"),
        ("三双", "生涯三双总数", "拉塞尔·威斯布鲁克", "203次", "2008-至今", "NBA历史三双王"),
        ("三双", "赛季三双次数", "拉塞尔·威斯布鲁克", "42次", "2016-17赛季", "单赛季三双纪录"),
        ("连胜", "最长连胜", "洛杉矶湖人", "33连胜", "1971-72赛季", "NBA最长连胜纪录"),
        ("总冠军", "最多总冠军(球队)", "波士顿凯尔特人/洛杉矶湖人", "18次/17次", "历史", "凯尔特人18冠，湖人17冠"),
        ("总冠军", "最多总冠军(球员)", "比尔·拉塞尔", "11次", "1956-1969", "指环王拉塞尔11枚冠军戒指"),
        ("MVP", "最多常规赛MVP", "卡里姆·贾巴尔", "6次", "1970-1986", "天勾贾巴尔6次MVP"),
        ("FMVP", "最多总决赛MVP", "迈克尔·乔丹", "6次", "1991-1998", "乔丹6次FMVP，6次总决赛全胜"),
        ("得分王", "最多得分王", "迈克尔·乔丹", "10次", "1986-1998", "乔丹10次得分王"),
        ("DPOY", "最多最佳防守球员", "鲁迪·戈贝尔/迪肯贝·穆托姆博/本·华莱士", "4次", "历史", "三人并列4次DPOY"),
        ("全明星", "最多全明星入选", "勒布朗·詹姆斯", "21次", "2003-至今", "詹姆斯连续21次入选全明星"),
        ("其他", "最高身高", "马努特·波尔/乔治·穆雷桑", "231cm", "历史", "NBA历史最高球员"),
        ("其他", "最年轻得分王", "凯文·杜兰特", "21岁", "2009-10赛季", "最年轻的得分王"),
        ("其他", "最年轻MVP", "德里克·罗斯", "22岁", "2010-11赛季", "最年轻的常规赛MVP"),
    ]
    c.executemany("INSERT INTO records (category, record_type, holder, value, season, description) VALUES (?, ?, ?, ?, ?, ?)", records)


def _seed_mvp(c):
    mvps = [
        (2026, "尼古拉·约基奇", "丹佛掘金", "常规赛MVP"),
        (2025, "谢伊·吉尔杰斯-亚历山大", "俄克拉荷马雷霆", "常规赛MVP"),
        (2024, "尼古拉·约基奇", "丹佛掘金", "常规赛MVP"),
        (2023, "乔尔·恩比德", "费城76人", "常规赛MVP"),
        (2022, "尼古拉·约基奇", "丹佛掘金", "常规赛MVP"),
        (2021, "尼古拉·约基奇", "丹佛掘金", "常规赛MVP"),
        (2020, "扬尼斯·阿德托昆博", "密尔沃基雄鹿", "常规赛MVP"),
        (2019, "扬尼斯·阿德托昆博", "密尔沃基雄鹿", "常规赛MVP"),
        (2018, "詹姆斯·哈登", "休斯顿火箭", "常规赛MVP"),
        (2017, "拉塞尔·威斯布鲁克", "俄克拉荷马雷霆", "常规赛MVP"),
        (2016, "斯蒂芬·库里", "金州勇士", "常规赛MVP"),
        (2015, "斯蒂芬·库里", "金州勇士", "常规赛MVP"),
        (2014, "凯文·杜兰特", "俄克拉荷马雷霆", "常规赛MVP"),
        (2013, "勒布朗·詹姆斯", "迈阿密热火", "常规赛MVP"),
        (2012, "勒布朗·詹姆斯", "迈阿密热火", "常规赛MVP"),
        (2011, "德里克·罗斯", "芝加哥公牛", "常规赛MVP"),
        (2010, "勒布朗·詹姆斯", "克利夫兰骑士", "常规赛MVP"),
        (2009, "勒布朗·詹姆斯", "克利夫兰骑士", "常规赛MVP"),
        (2008, "科比·布莱恩特", "洛杉矶湖人", "常规赛MVP"),
        (2007, "德克·诺维茨基", "达拉斯独行侠", "常规赛MVP"),
        (2006, "史蒂夫·纳什", "菲尼克斯太阳", "常规赛MVP"),
        (2005, "史蒂夫·纳什", "菲尼克斯太阳", "常规赛MVP"),
        (2004, "凯文·加内特", "明尼苏达森林狼", "常规赛MVP"),
        (2003, "蒂姆·邓肯", "圣安东尼奥马刺", "常规赛MVP"),
        (2002, "蒂姆·邓肯", "圣安东尼奥马刺", "常规赛MVP"),
        (2001, "阿伦·艾弗森", "费城76人", "常规赛MVP"),
        (2000, "沙奎尔·奥尼尔", "洛杉矶湖人", "常规赛MVP"),
        (1999, "卡尔·马龙", "犹他爵士", "常规赛MVP"),
        (1998, "迈克尔·乔丹", "芝加哥公牛", "常规赛MVP"),
        (1997, "卡尔·马龙", "犹他爵士", "常规赛MVP"),
        (1996, "迈克尔·乔丹", "芝加哥公牛", "常规赛MVP"),
    ]
    c.executemany("INSERT INTO mvp_history (year, player, team, award_type) VALUES (?, ?, ?, ?)", mvps)


def _seed_faq(c):
    faqs = [
        ("NBA有几支球队", "NBA目前有30支球队，分为东部联盟15支和西部联盟15支。每个联盟又分为3个赛区，每个赛区5支球队。", "规则"),
        ("NBA赛季什么时候开始", "NBA常规赛通常在10月中下旬开始，到次年4月中旬结束。季后赛从4月下旬开始，总决赛通常在6月举行。", "规则"),
        ("NBA选秀规则", "NBA选秀通常在每年6月举行，共2轮60个选秀权。未进入季后赛的14支球队参与乐透抽签决定前14顺位。", "规则"),
        ("什么是工资帽", "NBA工资帽是联盟规定的球队薪资上限，2025-26赛季工资帽约为1.488亿美元。奢侈税线约为1.808亿美元。", "规则"),
        ("什么是三双", "三双是指一名球员在一场比赛中三项数据达到两位数，最常见的是得分、篮板和助攻。威斯布鲁克是历史三双王。", "规则"),
        ("NBA总决赛什么赛制", "NBA总决赛采用7场4胜制（2-2-1-1-1），常规赛战绩更好的球队拥有主场优势。", "规则"),
        ("什么是DPOY", "DPOY是年度最佳防守球员奖（Defensive Player of the Year），戈贝尔、穆托姆博和华莱士各获得4次，并列历史最多。", "奖项"),
        ("什么是FMVP", "FMVP是总决赛最有价值球员奖（Finals Most Valuable Player），乔丹6次获得该奖项，为历史最多。", "奖项"),
        ("什么是6MOTY", "6MOTY是年度最佳第六人奖（Sixth Man of the Year），颁发给替补席上贡献最大的球员。克劳福德和路威各3次获奖。", "奖项"),
        ("篮球场地多大", "NBA标准球场长94英尺（28.7米），宽50英尺（15.2米）。三分线距离篮筐23英尺9英寸（7.24米）。", "规则"),
        ("NBA全明星赛", "NBA全明星赛通常在2月举行，由球迷、球员和媒体投票选出东西部各12名球员参加。勒布朗·詹姆斯21次入选为历史最多。", "赛事"),
        ("什么是双向合同", "双向合同允许NBA球队额外签约2名球员，这些球员在NBA和发展联盟之间切换，薪资也相应调整。", "规则"),
    ]
    c.executemany("INSERT INTO faq (question_pattern, answer, category) VALUES (?, ?, ?)", faqs)


def _seed_career_stats(c):
    stats = [
        (1, 22, 1520, 42184, 11719, 11342, 2420, 1145, 27.7, 7.7, 7.5, 1.6, 0.8, 50.5, 34.6, 73.5, 38.1),
        (2, 16, 980, 23668, 4580, 6190, 1530, 420, 24.2, 4.7, 6.3, 1.6, 0.4, 47.3, 42.6, 91.0, 34.2),
        (3, 18, 1100, 29724, 7350, 4860, 1180, 1180, 27.0, 6.7, 4.4, 1.1, 1.1, 50.1, 38.6, 88.3, 36.8),
        (4, 12, 840, 18850, 7860, 3920, 920, 980, 22.4, 9.4, 4.7, 1.1, 1.2, 54.5, 28.4, 64.2, 33.5),
        (5, 10, 760, 16280, 8350, 5680, 760, 580, 21.4, 11.0, 7.5, 1.0, 0.8, 55.8, 34.2, 82.5, 33.2),
        (6, 7, 480, 12840, 3480, 3680, 480, 220, 26.8, 7.3, 7.7, 1.0, 0.5, 46.5, 34.8, 75.2, 34.8),
        (7, 13, 820, 18620, 8280, 2120, 1120, 1680, 22.7, 10.1, 2.6, 1.4, 2.1, 52.3, 30.8, 78.5, 34.5),
        (8, 15, 1020, 26180, 4860, 6820, 1620, 380, 25.7, 4.8, 6.7, 1.6, 0.4, 44.2, 36.4, 85.8, 35.2),
        (9, 17, 1140, 25380, 8280, 9820, 1860, 280, 22.3, 7.3, 8.6, 1.6, 0.2, 43.6, 30.8, 80.5, 34.5),
        (10, 13, 760, 14680, 4860, 2120, 1180, 780, 19.3, 6.4, 2.8, 1.6, 1.0, 49.5, 37.2, 82.0, 32.8),
        (11, 8, 560, 13860, 3280, 1860, 480, 280, 24.8, 5.9, 3.3, 0.9, 0.5, 46.2, 37.8, 84.5, 35.2),
        (12, 9, 620, 12880, 3420, 1680, 680, 280, 20.8, 5.5, 2.7, 1.1, 0.5, 47.8, 36.2, 72.5, 33.8),
        (13, 10, 520, 12840, 4860, 1860, 480, 1180, 24.7, 9.3, 3.6, 0.9, 2.3, 47.8, 33.8, 82.2, 32.5),
        (14, 10, 680, 15680, 2860, 2860, 620, 180, 23.1, 4.2, 4.2, 0.9, 0.3, 46.5, 36.2, 87.5, 34.5),
        (15, 12, 840, 21840, 3680, 6120, 1180, 280, 26.0, 4.4, 7.3, 1.4, 0.3, 43.8, 37.2, 89.5, 36.2),
        (16, 6, 380, 9680, 1680, 2480, 380, 120, 25.5, 4.4, 6.5, 1.0, 0.3, 46.8, 34.5, 76.2, 33.5),
        (17, 5, 340, 8680, 1860, 1680, 380, 180, 25.5, 5.5, 4.9, 1.1, 0.5, 46.2, 35.8, 78.5, 34.8),
        (18, 7, 480, 11860, 2280, 2480, 580, 280, 24.7, 4.8, 5.2, 1.2, 0.6, 48.5, 34.2, 86.5, 34.2),
        (19, 14, 880, 18680, 5860, 3280, 1580, 480, 21.2, 6.7, 3.7, 1.8, 0.5, 44.5, 37.8, 85.2, 34.5),
        (20, 13, 820, 15680, 4860, 3680, 1480, 380, 19.1, 5.9, 4.5, 1.8, 0.5, 46.2, 35.5, 84.5, 35.2),
        (21, 13, 780, 16860, 2860, 4680, 980, 220, 21.6, 3.7, 6.0, 1.3, 0.3, 46.8, 38.8, 88.5, 34.8),
        (22, 20, 1280, 22680, 4860, 12180, 2680, 180, 17.7, 3.8, 9.5, 2.1, 0.1, 47.2, 36.5, 87.2, 34.5),
        (23, 5, 280, 7680, 2860, 980, 380, 180, 27.4, 10.2, 3.5, 1.4, 0.6, 58.5, 33.8, 68.5, 32.5),
        (24, 8, 540, 10860, 1860, 2860, 680, 220, 20.1, 3.4, 5.3, 1.3, 0.4, 46.5, 34.2, 78.5, 33.8),
        (39, 13, 820, 16680, 3680, 2120, 980, 380, 20.3, 4.5, 2.6, 1.2, 0.5, 45.8, 41.2, 85.2, 34.2),
        (40, 13, 780, 9860, 5280, 3480, 1180, 680, 12.6, 6.8, 4.5, 1.5, 0.9, 45.2, 31.8, 70.5, 31.8),
    ]
    c.executemany("""INSERT INTO career_stats 
        (player_id, seasons, games_played, total_points, total_rebounds, total_assists, total_steals, total_blocks,
         ppg, rpg, apg, spg, bpg, fg_pct, three_pct, ft_pct, mpg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", stats)


def _seed_season_stats(c):
    season_stats = [
        (1, "2025-26", "LAL", 45, 23.8, 7.5, 8.0, 0.9, 0.5, 49.2, 34.8, 74.2, 34.5),
        (2, "2025-26", "GSW", 42, 22.1, 5.0, 6.5, 1.0, 0.3, 44.8, 41.2, 92.0, 32.5),
        (3, "2025-26", "PHX", 40, 26.5, 6.0, 4.2, 0.7, 1.1, 51.8, 38.2, 86.5, 36.0),
        (4, "2025-26", "MIL", 43, 28.2, 11.2, 5.5, 0.8, 1.1, 55.5, 25.2, 62.0, 33.2),
        (5, "2025-26", "DEN", 44, 25.0, 12.5, 8.8, 1.1, 0.5, 57.0, 34.2, 82.5, 34.5),
        (6, "2025-26", "LAL", 35, 27.8, 8.0, 7.5, 1.7, 0.4, 46.5, 34.0, 76.0, 35.2),
        (7, "2025-26", "LAL", 42, 24.5, 11.2, 3.0, 1.1, 2.0, 52.2, 28.5, 78.0, 35.0),
        (18, "2025-26", "OKC", 48, 32.5, 4.8, 6.2, 1.6, 0.9, 51.5, 37.0, 89.5, 34.0),
        (17, "2025-26", "MIN", 46, 27.2, 5.5, 4.0, 1.1, 0.4, 46.0, 38.2, 82.0, 35.5),
        (11, "2025-26", "BOS", 45, 26.5, 8.0, 4.5, 0.9, 0.4, 45.5, 36.0, 84.0, 36.0),
        (12, "2025-26", "BOS", 44, 22.2, 6.0, 4.2, 1.1, 0.4, 47.0, 35.5, 72.0, 34.2),
        (29, "2025-26", "SAS", 38, 24.0, 10.5, 3.5, 1.1, 3.5, 47.2, 32.5, 82.0, 32.2),
    ]
    c.executemany("""INSERT INTO season_stats 
        (player_id, season, team_abbr, games, ppg, rpg, apg, spg, bpg, fg_pct, three_pct, ft_pct, mpg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", season_stats)


def query_player(name: str) -> Optional[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM players WHERE name_cn=? OR name_en=? OR aliases LIKE ?", (name, name, f"%{name}%"))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def query_player_stats(name: str) -> Optional[Dict]:
    player = query_player(name)
    if not player:
        return None
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM career_stats WHERE player_id=?", (player['id'],))
    row = c.fetchone()
    conn.close()
    if row:
        result = dict(row)
        result['player'] = player
        return result
    return None


def query_player_season_stats(name: str, season: str = None) -> List[Dict]:
    player = query_player(name)
    if not player:
        return []
    conn = get_connection()
    c = conn.cursor()
    if season:
        c.execute("SELECT * FROM season_stats WHERE player_id=? AND season=?", (player['id'], season))
    else:
        c.execute("SELECT * FROM season_stats WHERE player_id=? ORDER BY season DESC", (player['id'],))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_team(abbr: str) -> Optional[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM teams WHERE abbr=? OR name_cn LIKE ? OR name_en LIKE ?", (abbr.upper(), f"%{abbr}%", f"%{abbr}%"))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None


def query_champions(year: int = None) -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    if year:
        c.execute("SELECT * FROM champions WHERE year=?", (year,))
    else:
        c.execute("SELECT * FROM champions ORDER BY year DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_records(category: str = None) -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    if category:
        c.execute("SELECT * FROM records WHERE category=?", (category,))
    else:
        c.execute("SELECT * FROM records")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_mvp(year: int = None, player: str = None) -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    if year:
        c.execute("SELECT * FROM mvp_history WHERE year=?", (year,))
    elif player:
        c.execute("SELECT * FROM mvp_history WHERE player LIKE ?", (f"%{player}%",))
    else:
        c.execute("SELECT * FROM mvp_history ORDER BY year DESC LIMIT 20")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_faq(question: str) -> Optional[str]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM faq")
    rows = c.fetchall()
    conn.close()
    for row in rows:
        r = dict(row)
        patterns = r['question_pattern'].split(',')
        for p in patterns:
            if p.strip() in question:
                return r['answer']
    return None


def query_all_players() -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM players ORDER BY name_cn")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def query_all_teams() -> List[Dict]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM teams ORDER BY conference, name_cn")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def compare_two_players(name1: str, name2: str) -> Optional[Dict]:
    p1 = query_player_stats(name1)
    p2 = query_player_stats(name2)
    if not p1 or not p2:
        return None
    return {"player1": p1, "player2": p2}


if __name__ == "__main__":
    init_database()
    print("=== 数据库测试 ===\n")

    print("球员查询:")
    p = query_player("詹姆斯")
    if p:
        print(f"  {p['name_cn']} ({p['name_en']}) - {p['position']} - {p['team_abbr']}")

    print("\n生涯数据:")
    s = query_player_stats("库里")
    if s:
        print(f"  {s['player']['name_cn']}: {s['ppg']}分 {s['rpg']}板 {s['apg']}助")

    print("\n球队查询:")
    t = query_team("LAL")
    if t:
        print(f"  {t['name_cn']} - {t['championships']}次总冠军")

    print("\n冠军查询:")
    ch = query_champions(2024)
    for c in ch:
        print(f"  {c['year']}年冠军: {c['champion']}")

    print("\n纪录查询:")
    rec = query_records("得分")
    for r in rec:
        print(f"  {r['record_type']}: {r['holder']} - {r['value']}")

    print("\nFAQ查询:")
    faq = query_faq("NBA有几支球队")
    if faq:
        print(f"  {faq}")

    print("\n球员对比:")
    cmp = compare_two_players("詹姆斯", "库里")
    if cmp:
        p1, p2 = cmp['player1'], cmp['player2']
        print(f"  {p1['player']['name_cn']}: {p1['ppg']}分 vs {p2['player']['name_cn']}: {p2['ppg']}分")
