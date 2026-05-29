#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class KnowledgeItem:
    """知识条目"""
    id: str
    content: str
    category: str  # player, team, history, rule, record
    metadata: Dict
    embedding: Optional[List[float]] = None


class SimpleEmbedding:
    """简单的词频嵌入（无需外部模型）"""
    
    def __init__(self):
        self.vocab = {}
        self.vocab_size = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """简单分词"""
        # 中文按字分词，英文按空格分词
        import re
        # 分离中英文
        tokens = []
        for char in text.lower():
            if '\u4e00' <= char <= '\u9fff':  # 中文字符
                tokens.append(char)
            elif char.isalnum():
                tokens.append(char)
        return tokens
    
    def get_embedding(self, text: str) -> List[float]:
        """获取文本的嵌入向量（基于TF-IDF思想）"""
        tokens = self._tokenize(text)
        
        # 使用简单的词频统计
        word_freq = {}
        for token in tokens:
            word_freq[token] = word_freq.get(token, 0) + 1
        
        # 构建固定长度的向量（使用哈希）
        vector_size = 128
        vector = [0.0] * vector_size
        
        for word, freq in word_freq.items():
            # 使用哈希确定位置
            hash_val = hash(word) % vector_size
            vector[hash_val] += freq
        
        # 归一化
        norm = sum(x ** 2 for x in vector) ** 0.5
        if norm > 0:
            vector = [x / norm for x in vector]
        
        return vector


class NBAKnowledgeBase:
    """NBA知识库"""
    
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir or os.path.join(os.path.dirname(__file__), '..', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.embedding = SimpleEmbedding()
        self.knowledge_items: List[KnowledgeItem] = []
        self.knowledge_file = os.path.join(self.data_dir, 'knowledge_base.json')
        
        self._init_knowledge()
    
    def _init_knowledge(self):
        """初始化知识库"""
        if os.path.exists(self.knowledge_file):
            self._load_knowledge()
        else:
            self._build_default_knowledge()
            self._save_knowledge()
    
    def _build_default_knowledge(self):
        """构建默认知识库"""
        logger.info("构建默认NBA知识库...")
        
        # 历史冠军
        champions_data = [
            {"year": "2024", "champion": "波士顿凯尔特人", "mvp": "杰伦·布朗", "finals_mvp": "杰伦·布朗"},
            {"year": "2023", "champion": "丹佛掘金", "mvp": "尼古拉·约基奇", "finals_mvp": "尼古拉·约基奇"},
            {"year": "2022", "champion": "金州勇士", "mvp": "尼古拉·约基奇", "finals_mvp": "斯蒂芬·库里"},
            {"year": "2021", "champion": "密尔沃基雄鹿", "mvp": "尼古拉·约基奇", "finals_mvp": "扬尼斯·阿德托昆博"},
            {"year": "2020", "champion": "洛杉矶湖人", "mvp": "扬尼斯·阿德托昆博", "finals_mvp": "勒布朗·詹姆斯"},
            {"year": "2019", "champion": "多伦多猛龙", "mvp": "扬尼斯·阿德托昆博", "finals_mvp": "科怀·伦纳德"},
            {"year": "2018", "champion": "金州勇士", "mvp": "詹姆斯·哈登", "finals_mvp": "凯文·杜兰特"},
            {"year": "2017", "champion": "金州勇士", "mvp": "拉塞尔·威斯布鲁克", "finals_mvp": "凯文·杜兰特"},
            {"year": "2016", "champion": "克利夫兰骑士", "mvp": "斯蒂芬·库里", "finals_mvp": "勒布朗·詹姆斯"},
            {"year": "2015", "champion": "金州勇士", "mvp": "斯蒂芬·库里", "finals_mvp": "安德烈·伊戈达拉"},
        ]
        
        for data in champions_data:
            content = f"{data['year']}年NBA总冠军是{data['champion']}，常规赛MVP是{data['mvp']}，总决赛MVP是{data['finals_mvp']}。"
            item = KnowledgeItem(
                id=f"champion_{data['year']}",
                content=content,
                category="history",
                metadata=data
            )
            item.embedding = self.embedding.get_embedding(content)
            self.knowledge_items.append(item)
        
        # 历史MVP
        mvp_data = [
            {"year": "2024", "player": "尼古拉·约基奇", "team": "丹佛掘金"},
            {"year": "2023", "player": "乔尔·恩比德", "team": "费城76人"},
            {"year": "2022", "player": "尼古拉·约基奇", "team": "丹佛掘金"},
            {"year": "2021", "player": "尼古拉·约基奇", "team": "丹佛掘金"},
            {"year": "2020", "player": "扬尼斯·阿德托昆博", "team": "密尔沃基雄鹿"},
            {"year": "2019", "player": "扬尼斯·阿德托昆博", "team": "密尔沃基雄鹿"},
            {"year": "2018", "player": "詹姆斯·哈登", "team": "休斯顿火箭"},
            {"year": "2017", "player": "拉塞尔·威斯布鲁克", "team": "俄克拉荷马雷霆"},
            {"year": "2016", "player": "斯蒂芬·库里", "team": "金州勇士"},
            {"year": "2015", "player": "斯蒂芬·库里", "team": "金州勇士"},
            {"year": "2014", "player": "凯文·杜兰特", "team": "俄克拉荷马雷霆"},
            {"year": "2013", "player": "勒布朗·詹姆斯", "team": "迈阿密热火"},
            {"year": "2012", "player": "勒布朗·詹姆斯", "team": "迈阿密热火"},
            {"year": "2011", "player": "德里克·罗斯", "team": "芝加哥公牛"},
            {"year": "2010", "player": "勒布朗·詹姆斯", "team": "克利夫兰骑士"},
        ]
        
        for data in mvp_data:
            content = f"{data['year']}年NBA常规赛MVP是{data['player']}，来自{data['team']}。"
            item = KnowledgeItem(
                id=f"mvp_{data['year']}",
                content=content,
                category="history",
                metadata=data
            )
            item.embedding = self.embedding.get_embedding(content)
            self.knowledge_items.append(item)
        
        # 球员知识
        player_knowledge = [
            {
                "id": "player_lebron",
                "content": "勒布朗·詹姆斯（LeBron James），绰号'小皇帝'、'老詹'，现役NBA球员，效力于洛杉矶湖人。4次NBA总冠军，4次MVP，历史得分王。",
                "category": "player",
                "metadata": {"name": "勒布朗·詹姆斯", "aliases": ["詹姆斯", "老詹", "詹皇", "小皇帝"]}
            },
            {
                "id": "player_curry",
                "content": "斯蒂芬·库里（Stephen Curry），绰号'萌神'、'小学生'，金州勇士当家球星。历史三分王，4次总冠军，2次MVP，改变了现代篮球打法。",
                "category": "player",
                "metadata": {"name": "斯蒂芬·库里", "aliases": ["库里", "萌神", "小学生", "Chef Curry"]}
            },
            {
                "id": "player_durant",
                "content": "凯文·杜兰特（Kevin Durant），绰号'死神'、'KD'，菲尼克斯太阳球星。2次总冠军，2次FMVP，4次得分王，历史顶级得分手。",
                "category": "player",
                "metadata": {"name": "凯文·杜兰特", "aliases": ["杜兰特", "KD", "死神", "书包杜"]}
            },
            {
                "id": "player_jokic",
                "content": "尼古拉·约基奇（Nikola Jokic），绰号'约老师'，丹佛掘金当家球星。3次MVP，1次总冠军，历史级中锋，传球视野极佳。",
                "category": "player",
                "metadata": {"name": "尼古拉·约基奇", "aliases": ["约基奇", "约老师", "小丑"]}
            },
            {
                "id": "player_giannis",
                "content": "扬尼斯·阿德托昆博（Giannis Antetokounmpo），绰号'字母哥'，密尔沃基雄鹿当家球星。2次MVP，1次总冠军，身体素质惊人。",
                "category": "player",
                "metadata": {"name": "扬尼斯·阿德托昆博", "aliases": ["字母哥", "希腊怪兽", "Greek Freak"]}
            },
        ]
        
        for data in player_knowledge:
            item = KnowledgeItem(
                id=data["id"],
                content=data["content"],
                category=data["category"],
                metadata=data["metadata"]
            )
            item.embedding = self.embedding.get_embedding(data["content"])
            self.knowledge_items.append(item)
        
        # 球队知识
        team_knowledge = [
            {
                "id": "team_lakers",
                "content": "洛杉矶湖人（Los Angeles Lakers）是NBA历史最辉煌的球队之一，位于加州洛杉矶。17次总冠军，与凯尔特人并列历史第一。传奇球星包括科比、魔术师、詹姆斯等。",
                "category": "team",
                "metadata": {"name": "洛杉矶湖人", "aliases": ["湖人", "Lakers", "紫金军团"]}
            },
            {
                "id": "team_celtics",
                "content": "波士顿凯尔特人（Boston Celtics）是NBA传统豪门，17次总冠军。球队文化强调团队篮球和防守。",
                "category": "team",
                "metadata": {"name": "波士顿凯尔特人", "aliases": ["凯尔特人", "Celtics", "绿军"]}
            },
            {
                "id": "team_warriors",
                "content": "金州勇士（Golden State Warriors）近年来最成功球队之一，4次总冠军（2015、2017、2018、2022）。以三分投射和快节奏进攻著称。",
                "category": "team",
                "metadata": {"name": "金州勇士", "aliases": ["勇士", "Warriors", "宇宙勇"]}
            },
        ]
        
        for data in team_knowledge:
            item = KnowledgeItem(
                id=data["id"],
                content=data["content"],
                category=data["category"],
                metadata=data["metadata"]
            )
            item.embedding = self.embedding.get_embedding(data["content"])
            self.knowledge_items.append(item)
        
        # 规则知识
        rule_knowledge = [
            {
                "id": "rule_format",
                "content": "NBA常规赛每队打82场比赛，分东部和西部两个联盟，每个联盟3个赛区。季后赛采用7场4胜制，共16支球队参加。",
                "category": "rule",
                "metadata": {"topic": "赛制"}
            },
            {
                "id": "rule_awards",
                "content": "NBA主要奖项包括：常规赛MVP、总决赛FMVP、最佳防守球员DPOY、最佳新秀ROY、最佳第六人、最快进步球员等。",
                "category": "rule",
                "metadata": {"topic": "奖项"}
            },
            {
                "id": "rule_stats",
                "content": "NBA主要统计数据：得分（PTS）、篮板（REB）、助攻（AST）、抢断（STL）、盖帽（BLK）、投篮命中率（FG%）、三分命中率（3P%）、罚球命中率（FT%）。",
                "category": "rule",
                "metadata": {"topic": "统计"}
            },
        ]
        
        for data in rule_knowledge:
            item = KnowledgeItem(
                id=data["id"],
                content=data["content"],
                category=data["category"],
                metadata=data["metadata"]
            )
            item.embedding = self.embedding.get_embedding(data["content"])
            self.knowledge_items.append(item)
        
        logger.info(f"知识库构建完成，共 {len(self.knowledge_items)} 条知识")
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return dot_product
    
    def search(self, query: str, top_k: int = 3) -> List[KnowledgeItem]:
        """搜索相关知识"""
        query_embedding = self.embedding.get_embedding(query)
        
        # 计算相似度
        similarities = []
        for item in self.knowledge_items:
            if item.embedding:
                sim = self._cosine_similarity(query_embedding, item.embedding)
                similarities.append((item, sim))
        
        # 排序并返回前k个
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [item for item, sim in similarities[:top_k] if sim > 0.1]
    
    def get_context(self, query: str, max_items: int = 3) -> str:
        """获取查询相关的上下文"""
        results = self.search(query, max_items)
        
        if not results:
            return ""
        
        context = "【NBA知识库参考信息】\n"
        for i, item in enumerate(results, 1):
            context += f"{i}. {item.content}\n"
        
        return context
    
    def add_knowledge(self, content: str, category: str, metadata: Dict = None) -> str:
        """添加新知识"""
        item_id = f"custom_{len(self.knowledge_items)}"
        item = KnowledgeItem(
            id=item_id,
            content=content,
            category=category,
            metadata=metadata or {}
        )
        item.embedding = self.embedding.get_embedding(content)
        self.knowledge_items.append(item)
        
        self._save_knowledge()
        return item_id
    
    def _save_knowledge(self):
        """保存知识库到文件"""
        data = []
        for item in self.knowledge_items:
            data.append({
                "id": item.id,
                "content": item.content,
                "category": item.category,
                "metadata": item.metadata,
                "embedding": item.embedding
            })
        
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"知识库已保存到 {self.knowledge_file}")
    
    def _load_knowledge(self):
        """从文件加载知识库"""
        with open(self.knowledge_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item_data in data:
            item = KnowledgeItem(
                id=item_data["id"],
                content=item_data["content"],
                category=item_data["category"],
                metadata=item_data["metadata"],
                embedding=item_data.get("embedding")
            )
            self.knowledge_items.append(item)
        
        logger.info(f"知识库已加载，共 {len(self.knowledge_items)} 条知识")


# 全局知识库实例
knowledge_base = NBAKnowledgeBase()


def get_knowledge_context(query: str) -> str:
    """获取知识库上下文（便捷函数）"""
    return knowledge_base.get_context(query)


def search_knowledge(query: str, top_k: int = 3) -> List[Dict]:
    """搜索知识库（便捷函数）"""
    results = knowledge_base.search(query, top_k)
    return [
        {
            "content": r.content,
            "category": r.category,
            "metadata": r.metadata
        }
        for r in results
    ]


if __name__ == "__main__":
    print("=== NBA知识库测试 ===\n")
    
    # 测试搜索
    test_queries = [
        "谁是去年的总冠军？",
        "库里有什么成就？",
        "MVP是什么意思？",
        "湖人有多少个冠军？",
        "约基奇是谁？",
    ]
    
    for query in test_queries:
        print(f"\n查询: {query}")
        context = knowledge_base.get_context(query)
        if context:
            print(f"找到相关知识:\n{context}")
        else:
            print("未找到相关知识")
