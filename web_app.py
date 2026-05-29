import sys
import os
import json

# 添加项目路径和 flask_lib 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_lib'))

from flask import Flask, render_template_string, request, jsonify, Response
from config import config
from modules.llm import (
    chat, 
    chat_with_context, 
    chat_with_context_stream,
    is_data_query, 
    extract_entities,
    get_intent
)
from modules.nba_live_data import (
    get_player_info,
    get_standings,
    get_today_games,
    get_team_schedule,
    get_league_leaders,
    compare_players
)
from modules.voice import text_to_speech
from modules.local_answer import local_answer, can_answer_locally
from modules.local_database import init_database
import base64
import tempfile

app = Flask(__name__)

CONVERSATION_HISTORY = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏀 NBA智能助手 v2.2</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #ff6b35;
            font-size: 2.5em;
            margin-bottom: 5px;
        }
        .subtitle {
            text-align: center;
            color: #aaa;
            margin-bottom: 20px;
            font-size: 0.9em;
        }
        .status-bar {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            font-size: 0.85em;
        }
        .status-item {
            background: rgba(255,255,255,0.1);
            padding: 5px 15px;
            border-radius: 15px;
        }
        .status-item.active { color: #4ade80; }
        .status-item.inactive { color: #f87171; }
        .chat-container {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            height: 450px;
            overflow-y: auto;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        .message {
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 10px;
            animation: fadeIn 0.3s ease;
            line-height: 1.6;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .user-message {
            background: rgba(255,107,53,0.2);
            margin-left: 20%;
            border-left: 3px solid #ff6b35;
        }
        .ai-message {
            background: rgba(255,255,255,0.1);
            margin-right: 20%;
            border-left: 3px solid #4ade80;
        }
        .ai-message pre {
            background: rgba(0,0,0,0.3);
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
            white-space: pre-wrap;
            font-family: inherit;
        }
        .input-container {
            display: flex;
            gap: 10px;
        }
        input[type="text"] {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        input[type="text"]:focus {
            outline: 2px solid #ff6b35;
        }
        button {
            padding: 15px 30px;
            background: #ff6b35;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: bold;
        }
        button:hover { 
            background: #ff8c5a;
            transform: translateY(-2px);
        }
        button:disabled {
            background: #666;
            cursor: not-allowed;
            transform: none;
        }
        .loading {
            text-align: center;
            color: #aaa;
            padding: 10px;
        }
        .loading::after {
            content: '...';
            animation: dots 1.5s infinite;
        }
        @keyframes dots {
            0%, 20% { content: '.'; }
            40% { content: '..'; }
            60%, 100% { content: '...'; }
        }
        .examples {
            margin-top: 20px;
            text-align: center;
        }
        .examples-title {
            color: #aaa;
            margin-bottom: 10px;
            font-size: 0.9em;
        }
        .examples button {
            padding: 8px 15px;
            margin: 5px;
            background: rgba(255,255,255,0.2);
            font-size: 14px;
            font-weight: normal;
        }
        .examples button:hover { 
            background: rgba(255,255,255,0.3);
        }
        .typing-indicator {
            display: inline-block;
        }
        .typing-indicator span {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #ff6b35;
            border-radius: 50%;
            margin: 0 2px;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
        .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        .clear-btn {
            background: rgba(255,255,255,0.1);
            padding: 8px 15px;
            font-size: 12px;
            position: absolute;
            right: 20px;
            top: 20px;
        }
        header {
            position: relative;
        }
        .voice-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px;
            min-width: 50px;
            border-radius: 50%;
            font-size: 20px;
        }
        .voice-btn:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
            transform: scale(1.1);
        }
        .voice-btn.recording {
            background: #ff4757;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 71, 87, 0.7); }
            70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(255, 71, 87, 0); }
            100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(255, 71, 87, 0); }
        }
        .voice-controls {
            display: flex;
            gap: 10px;
            align-items: center;
            margin-top: 10px;
        }
        .voice-toggle {
            display: flex;
            align-items: center;
            gap: 5px;
            cursor: pointer;
            padding: 8px 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            font-size: 14px;
            transition: all 0.3s;
        }
        .voice-toggle:hover {
            background: rgba(255,255,255,0.2);
        }
        .voice-toggle.active {
            background: rgba(102, 126, 234, 0.5);
        }
        .voice-status {
            font-size: 12px;
            color: #aaa;
            margin-left: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏀 NBA智能助手</h1>
            <p class="subtitle">基于LLM + 实时NBA数据的智能问答系统</p>
            <button class="clear-btn" onclick="clearChat()">清空对话</button>
        </header>
        
        <div class="status-bar">
            <span class="status-item active">🤖 模型: """ + config.LLM_PROVIDER + """</span>
            <span class="status-item """ + ("active" if config.USE_LIVE_DATA else "inactive") + """">
                📊 实时数据: """ + ("已启用" if config.USE_LIVE_DATA else "未启用") + """
            </span>
        </div>
        
        <div class="chat-container" id="chat">
            <div class="message ai-message">
                👋 你好！我是NBA智能助手，可以帮你查询：
                <br><br>
                📅 <strong>比赛信息</strong> - 今天有哪些比赛？湖人赛程？
                <br>🏆 <strong>排名情况</strong> - NBA排名？东部战绩？
                <br>👤 <strong>球员数据</strong> - 詹姆斯数据？库里场均得分？
                <br>📊 <strong>排行榜</strong> - 得分榜前十？篮板王？
                <br>⚔️ <strong>球员对比</strong> - 詹姆斯和库里谁更强？
                <br><br>
                💡 支持别名：老詹、KD、字母哥、浓眉、华子等
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="userInput" placeholder="输入你的问题，或点击麦克风语音输入..." onkeypress="handleKeyPress(event)">
            <button id="voiceBtn" class="voice-btn" onclick="toggleVoiceInput()" title="语音输入">🎤</button>
            <button id="sendBtn" onclick="sendMessage()">发送</button>
        </div>
        
        <div class="voice-controls">
            <div class="voice-toggle" id="voiceToggle" onclick="toggleVoiceOutput()">
                <span id="voiceToggleIcon">🔊</span>
                <span id="voiceToggleText">语音播报: 关闭</span>
            </div>
            <span class="voice-status" id="voiceStatus"></span>
        </div>
        
        <div class="examples">
            <p class="examples-title">快捷查询：</p>
            <button onclick="sendQuick('今天有哪些比赛？')">📅 今日比赛</button>
            <button onclick="sendQuick('NBA排名')">🏆 排名</button>
            <button onclick="sendQuick('得分榜前十')">📊 得分榜</button>
            <button onclick="sendQuick('詹姆斯数据')">👤 詹姆斯</button>
            <button onclick="sendQuick('湖人赛程')">📅 湖人赛程</button>
            <button onclick="sendQuick('詹姆斯和库里谁更强')">⚔️ 球员对比</button>
        </div>
    </div>
    
    <script>
        let isStreaming = false;
        
        function handleKeyPress(e) {
            if (e.key === 'Enter' && !isStreaming) sendMessage();
        }
        
        function sendQuick(text) {
            if (isStreaming) return;
            document.getElementById('userInput').value = text;
            sendMessage();
        }
        
        function clearChat() {
            const chat = document.getElementById('chat');
            chat.innerHTML = `
                <div class="message ai-message">
                    👋 对话已清空，有什么可以帮你的？
                </div>
            `;
            fetch('/clear', {method: 'POST'});
        }
        
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message || isStreaming) return;
            
            const chat = document.getElementById('chat');
            const sendBtn = document.getElementById('sendBtn');
            
            chat.innerHTML += '<div class="message user-message">' + escapeHtml(message) + '</div>';
            
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div> AI思考中';
            chat.appendChild(loadingDiv);
            chat.scrollTop = chat.scrollHeight;
            
            input.value = '';
            sendBtn.disabled = true;
            isStreaming = true;
            
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.className = 'message ai-message';
            
            try {
                const response = await fetch('/chat_stream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                
                loadingDiv.remove();
                chat.appendChild(aiMessageDiv);
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullContent = '';
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                if (data.content) {
                                    fullContent += data.content;
                                    aiMessageDiv.innerHTML = formatContent(fullContent);
                                    chat.scrollTop = chat.scrollHeight;
                                }
                                if (data.done) {
                                    break;
                                }
                            } catch (e) {}
                        }
                    }
                }
                
                if (!fullContent) {
                    aiMessageDiv.innerHTML = '抱歉，未能获取回复';
                }
                
            } catch (error) {
                loadingDiv.remove();
                chat.innerHTML += '<div class="message ai-message">抱歉，出现错误: ' + escapeHtml(error.toString()) + '</div>';
            }
            
            sendBtn.disabled = false;
            isStreaming = false;
            chat.scrollTop = chat.scrollHeight;
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function formatContent(content) {
            content = escapeHtml(content);
            content = content.replace(/\\n/g, '<br>');
            content = content.replace(/(📊|🏆|📅|👤|🏀|⚔️|💡|👋|🔍|📡)/g, '<span style="font-size:1.2em">$1</span>');
            return content;
        }
        
        // ==================== 语音功能 ====================
        let isVoiceOutputEnabled = false;
        let recognition = null;
        let isRecording = false;
        let currentAudio = null;
        
        // 初始化语音识别
        function initSpeechRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.lang = 'zh-CN';
                recognition.continuous = false;
                recognition.interimResults = false;
                
                recognition.onstart = function() {
                    isRecording = true;
                    document.getElementById('voiceBtn').classList.add('recording');
                    document.getElementById('voiceStatus').textContent = '🎙️ 正在录音，请说话...';
                };
                
                recognition.onresult = function(event) {
                    const transcript = event.results[0][0].transcript;
                    document.getElementById('userInput').value = transcript;
                    document.getElementById('voiceStatus').textContent = '✅ 识别成功，正在发送...';
                    // 自动发送
                    setTimeout(() => sendMessage(), 500);
                };
                
                recognition.onerror = function(event) {
                    console.error('语音识别错误:', event.error);
                    document.getElementById('voiceStatus').textContent = '❌ 识别失败，请重试';
                    stopRecording();
                };
                
                recognition.onend = function() {
                    stopRecording();
                };
                
                return true;
            } else {
                document.getElementById('voiceStatus').textContent = '⚠️ 浏览器不支持语音识别';
                return false;
            }
        }
        
        function stopRecording() {
            isRecording = false;
            document.getElementById('voiceBtn').classList.remove('recording');
            setTimeout(() => {
                if (!isRecording) {
                    document.getElementById('voiceStatus').textContent = '';
                }
            }, 2000);
        }
        
        function toggleVoiceInput() {
            if (!recognition) {
                if (!initSpeechRecognition()) {
                    alert('您的浏览器不支持语音识别功能，请使用 Chrome 或 Edge 浏览器');
                    return;
                }
            }
            
            if (isRecording) {
                recognition.stop();
            } else {
                try {
                    recognition.start();
                } catch (e) {
                    console.error('启动录音失败:', e);
                }
            }
        }
        
        function toggleVoiceOutput() {
            isVoiceOutputEnabled = !isVoiceOutputEnabled;
            const toggle = document.getElementById('voiceToggle');
            const icon = document.getElementById('voiceToggleIcon');
            const text = document.getElementById('voiceToggleText');
            
            if (isVoiceOutputEnabled) {
                toggle.classList.add('active');
                icon.textContent = '🔊';
                text.textContent = '语音播报: 开启';
                document.getElementById('voiceStatus').textContent = '🔊 已开启语音播报';
            } else {
                toggle.classList.remove('active');
                icon.textContent = '🔇';
                text.textContent = '语音播报: 关闭';
                document.getElementById('voiceStatus').textContent = '';
                // 停止当前播放
                if (currentAudio) {
                    currentAudio.pause();
                    currentAudio = null;
                }
            }
            
            setTimeout(() => {
                document.getElementById('voiceStatus').textContent = '';
            }, 2000);
        }
        
        // 播放语音
        async function playTextToSpeech(text) {
            if (!isVoiceOutputEnabled) return;
            
            try {
                // 停止之前的音频
                if (currentAudio) {
                    currentAudio.pause();
                    currentAudio = null;
                }
                
                document.getElementById('voiceStatus').textContent = '🔊 正在生成语音...';
                
                const response = await fetch('/tts', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({text: text})
                });
                
                const data = await response.json();
                
                if (data.success && data.audio) {
                    const audioData = 'data:audio/mp3;base64,' + data.audio;
                    currentAudio = new Audio(audioData);
                    
                    currentAudio.onplay = function() {
                        document.getElementById('voiceStatus').textContent = '🔊 正在播放...';
                    };
                    
                    currentAudio.onended = function() {
                        document.getElementById('voiceStatus').textContent = '';
                        currentAudio = null;
                    };
                    
                    currentAudio.onerror = function() {
                        document.getElementById('voiceStatus').textContent = '❌ 播放失败';
                        currentAudio = null;
                    };
                    
                    await currentAudio.play();
                } else {
                    document.getElementById('voiceStatus').textContent = '❌ 语音生成失败';
                }
            } catch (error) {
                console.error('TTS错误:', error);
                document.getElementById('voiceStatus').textContent = '❌ 语音服务异常';
            }
        }
        
        // 修改 sendMessage 函数，在回复完成后播放语音
        async function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message || isStreaming) return;
            
            const chat = document.getElementById('chat');
            const sendBtn = document.getElementById('sendBtn');
            
            chat.innerHTML += '<div class="message user-message">' + escapeHtml(message) + '</div>';
            
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'loading';
            loadingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div> AI思考中';
            chat.appendChild(loadingDiv);
            chat.scrollTop = chat.scrollHeight;
            
            input.value = '';
            sendBtn.disabled = true;
            isStreaming = true;
            
            const aiMessageDiv = document.createElement('div');
            aiMessageDiv.className = 'message ai-message';
            
            try {
                const response = await fetch('/chat_stream', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message: message})
                });
                
                loadingDiv.remove();
                chat.appendChild(aiMessageDiv);
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let fullContent = '';
                
                while (true) {
                    const {done, value} = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value);
                    const lines = chunk.split('\\n');
                    
                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                if (data.content) {
                                    fullContent += data.content;
                                    aiMessageDiv.innerHTML = formatContent(fullContent);
                                    chat.scrollTop = chat.scrollHeight;
                                }
                                if (data.done) {
                                    break;
                                }
                            } catch (e) {}
                        }
                    }
                }
                
                if (!fullContent) {
                    aiMessageDiv.innerHTML = '抱歉，未能获取回复';
                } else {
                    // 播放语音
                    if (isVoiceOutputEnabled) {
                        // 移除 HTML 标签，保留纯文本用于语音
                        const plainText = fullContent.replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ');
                        playTextToSpeech(plainText);
                    }
                }
                
            } catch (error) {
                loadingDiv.remove();
                chat.innerHTML += '<div class="message ai-message">抱歉，出现错误: ' + escapeHtml(error.toString()) + '</div>';
            }
            
            sendBtn.disabled = false;
            isStreaming = false;
            chat.scrollTop = chat.scrollHeight;
        }
    </script>
</body>
</html>
"""


def _check_llm_available() -> bool:
    try:
        from modules.llm import check_llm_status
        return check_llm_status()
    except Exception:
        api_key = getattr(config, 'DEEPSEEK_API_KEY', '')
        return bool(api_key and api_key.startswith('sk-'))


def handle_query(user_input: str) -> str:
    global CONVERSATION_HISTORY
    
    if len(CONVERSATION_HISTORY) > config.MAX_HISTORY * 2:
        CONVERSATION_HISTORY = CONVERSATION_HISTORY[-config.MAX_HISTORY * 2:]
    
    local_result = local_answer(user_input)
    if local_result:
        CONVERSATION_HISTORY.append(f"用户: {user_input}")
        CONVERSATION_HISTORY.append(f"AI: {local_result}")
        return local_result
    
    context = ""
    
    if is_data_query(user_input):
        entities = extract_entities(user_input)
        query_type = entities.get("query_type")
        intent = get_intent(user_input)
        
        if entities["players"]:
            for player in entities["players"]:
                player_info = get_player_info(player)
                context += f"\n{player_info}\n"
        
        if entities["teams"]:
            for team in entities["teams"]:
                team_info = get_team_schedule(team)
                context += f"\n{team_info}\n"
        
        if query_type == "today_games" or intent == "today_games":
            games = get_today_games()
            context += f"\n{games}\n"
        
        if query_type == "standings" or intent == "standings":
            standings = get_standings()
            context += f"\n{standings}\n"
        
        if query_type == "top_scorers":
            leaders = get_league_leaders("PTS", 10)
            context += f"\n{leaders}\n"
        
        if query_type == "top_rebounders":
            leaders = get_league_leaders("REB", 10)
            context += f"\n{leaders}\n"
        
        if query_type == "top_assists":
            leaders = get_league_leaders("AST", 10)
            context += f"\n{leaders}\n"
        
        if entities["comparison"] and len(entities["players"]) >= 2:
            comparison = compare_players(entities["players"][0], entities["players"][1])
            context += f"\n{comparison}\n"
        
        if context:
            history_context = "\n".join(CONVERSATION_HISTORY)
            full_context = f"历史对话:\n{history_context}\n\n最新数据:\n{context}" if history_context else context
            answer = chat_with_context(user_input, full_context)
        else:
            answer = chat(user_input)
    else:
        history_context = "\n".join(CONVERSATION_HISTORY)
        if history_context:
            answer = chat_with_context(user_input, f"历史对话:\n{history_context}")
        else:
            answer = chat(user_input)
    
    CONVERSATION_HISTORY.append(f"用户: {user_input}")
    CONVERSATION_HISTORY.append(f"AI: {answer}")
    
    return answer


def handle_query_stream(user_input: str):
    global CONVERSATION_HISTORY
    
    if len(CONVERSATION_HISTORY) > config.MAX_HISTORY * 2:
        CONVERSATION_HISTORY = CONVERSATION_HISTORY[-config.MAX_HISTORY * 2:]
    
    local_result = local_answer(user_input)
    if local_result:
        CONVERSATION_HISTORY.append(f"用户: {user_input}")
        CONVERSATION_HISTORY.append(f"AI: {local_result}")
        for char in local_result:
            yield f"data: {json.dumps({'content': char}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        return
    
    context = ""
    
    if is_data_query(user_input):
        entities = extract_entities(user_input)
        query_type = entities.get("query_type")
        intent = get_intent(user_input)
        
        if entities["players"]:
            for player in entities["players"]:
                player_info = get_player_info(player)
                context += f"\n{player_info}\n"
        
        if entities["teams"]:
            for team in entities["teams"]:
                team_info = get_team_schedule(team)
                context += f"\n{team_info}\n"
        
        if query_type == "today_games" or intent == "today_games":
            games = get_today_games()
            context += f"\n{games}\n"
        
        if query_type == "standings" or intent == "standings":
            standings = get_standings()
            context += f"\n{standings}\n"
        
        if query_type == "top_scorers":
            leaders = get_league_leaders("PTS", 10)
            context += f"\n{leaders}\n"
        
        if query_type == "top_rebounders":
            leaders = get_league_leaders("REB", 10)
            context += f"\n{leaders}\n"
        
        if query_type == "top_assists":
            leaders = get_league_leaders("AST", 10)
            context += f"\n{leaders}\n"
        
        if entities["comparison"] and len(entities["players"]) >= 2:
            comparison = compare_players(entities["players"][0], entities["players"][1])
            context += f"\n{comparison}\n"
    
    full_answer = ""
    history_context = "\n".join(CONVERSATION_HISTORY)
    
    if context:
        full_context = f"历史对话:\n{history_context}\n\n最新数据:\n{context}" if history_context else context
    else:
        full_context = f"历史对话:\n{history_context}" if history_context else ""
    
    for chunk in chat_with_context_stream(user_input, full_context):
        full_answer += chunk
        yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
    
    CONVERSATION_HISTORY.append(f"用户: {user_input}")
    CONVERSATION_HISTORY.append(f"AI: {full_answer}")
    
    yield f"data: {json.dumps({'done': True})}\n\n"


@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route('/chat', methods=['POST'])
def chat_endpoint():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({'response': '请输入问题'})
    
    try:
        answer = handle_query(user_input)
        return jsonify({'response': answer})
    except Exception as e:
        return jsonify({'response': f'抱歉，出错了: {str(e)}'})


@app.route('/chat_stream', methods=['POST'])
def chat_stream_endpoint():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return Response("data: " + json.dumps({'content': '请输入问题'}) + "\n\n", 
                       mimetype='text/event-stream')
    
    try:
        return Response(handle_query_stream(user_input), mimetype='text/event-stream')
    except Exception as e:
        return Response("data: " + json.dumps({'content': f'抱歉，出错了: {str(e)}'}) + "\n\n",
                       mimetype='text/event-stream')


@app.route('/clear', methods=['POST'])
def clear_history():
    global CONVERSATION_HISTORY
    CONVERSATION_HISTORY = []
    return jsonify({'status': 'ok'})


@app.route('/tts', methods=['POST'])
def text_to_speech_endpoint():
    """文字转语音接口"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        import asyncio
        import edge_tts
        
        async def generate_speech():
            voice = "zh-CN-XiaoxiaoNeural"
            communicate = edge_tts.Communicate(text, voice)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                temp_file = f.name
            await communicate.save(temp_file)
            
            with open(temp_file, 'rb') as f:
                audio_data = f.read()
            
            os.unlink(temp_file)
            return audio_data
        
        audio_data = asyncio.run(generate_speech())
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'format': 'mp3'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    init_database()
    
    port = 8083
    llm_available = _check_llm_available()
    
    print("=" * 50)
    print("🏀 NBA Web 助手 v2.2")
    print(f"   模型：{config.LLM_PROVIDER}")
    print(f"   LLM 服务：{'✅ 可用' if llm_available else '❌ 不可用（本地模式）'}")
    print(f"   本地数据库：✅ 已加载")
    print(f"   实时数据：{'开启' if config.USE_LIVE_DATA else '关闭'}")
    print("=" * 50)
    print(f"🌐 访问地址：http://localhost:{port}")
    if not llm_available:
        print("💡 提示：当前为本地模式，基础问题可直接回答")
        print("   配置API Key后可使用完整功能")
    print("=" * 50)
    app.run(host=config.WEB_HOST, port=port, debug=False, threaded=True)
