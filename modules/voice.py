#!/usr/bin/python3
# -*- coding: utf-8 -*-

import subprocess
import tempfile
import os
import speech_recognition as sr

def speech_to_text():
    try:
        print("🎤 请说话...")
        recognizer = sr.Recognizer()
        
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5)
        
        print("🔍 识别中...")
        text = recognizer.recognize_google(audio, language='zh-CN')
        print(f"✅ 识别结果: {text}")
        return text
        
    except sr.UnknownValueError:
        print("❌ 无法识别语音")
        return ""
    except sr.WaitTimeoutError:
        print("❌ 录音超时")
        return ""
    except Exception as e:
        print(f"❌ 错误: {e}")
        return ""

def text_to_speech(text):
    try:
        import asyncio
        import edge_tts
        
        async def speak():
            voice = "zh-CN-XiaoxiaoNeural"
            communicate = edge_tts.Communicate(text, voice)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                temp_file = f.name
            await communicate.save(temp_file)
            
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()
            os.unlink(temp_file)
        
        print(f"🔊 播报: {text[:20]}...")
        asyncio.run(speak())
        
    except Exception as e:
        print(f"❌ TTS错误: {e}")

if __name__ == "__main__":
    print("语音模块测试")
    text = speech_to_text()
    if text:
        text_to_speech(f"你说的是: {text}")
