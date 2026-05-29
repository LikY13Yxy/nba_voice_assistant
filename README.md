# NBA Voice Assistant

An intelligent NBA voice assistant powered by Large Language Models (LLM), featuring voice interaction, real-time NBA data queries, and intelligent dialogue capabilities.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [APIs & Data Sources](#apis--data-sources)
- [Docker Commands](#docker-commands)
- [Requirements](#requirements)

---

## Features

### Core Capabilities
- **Voice Interaction**: Natural voice conversations with speech recognition and text-to-speech
- **Real-time NBA Data**: Query player stats, team standings, game schedules, and league leaders
- **Intelligent Dialogue**: AI-powered conversations using state-of-the-art LLMs
- **Player Comparison**: Compare statistics between multiple players
- **Knowledge Base**: RAG (Retrieval-Augmented Generation) for NBA history and rules

### User Interfaces
- **Web Interface**: Clean, responsive web UI built with Flask
- **Voice Input**: Microphone support for hands-free interaction
- **Streaming Responses**: Real-time streaming text and voice responses

---

## Tech Stack

### Backend Framework
| Technology | Purpose | Version |
|------------|---------|---------|
| **Flask** | Web framework for REST API and web interface | >=3.0.0 |
| **Python** | Programming language | 3.11+ |

### AI & LLM Integration
| Technology | Purpose |
|------------|---------|
| **DeepSeek API** | Primary LLM for intelligent dialogue and analysis |
| **OpenAI API** | Alternative LLM provider (SiliconFlow compatible) |
| **Ollama** | Local LLM deployment option |
| **RAG (Retrieval-Augmented Generation)** | Knowledge base enhancement for NBA facts |

### Voice Processing
| Technology | Purpose | Version |
|------------|---------|---------|
| **SpeechRecognition** | Speech-to-text conversion | >=3.8.1 |
| **Edge-TTS** | Text-to-speech synthesis | >=6.1.12 |
| **Pygame** | Audio playback | >=2.5.0 |

### Data Sources
| Technology | Purpose |
|------------|---------|
| **NBA API** | Official NBA statistics and data |
| **BallDontLie API** | Free NBA statistics API (fallback) |
| **nba_api** | Python wrapper for NBA.com API | >=1.4.1 |

### DevOps & Deployment
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization for consistent environments |
| **Docker Compose** | Multi-container orchestration |
| **Git** | Version control |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Web UI     │  │ Voice Input  │  │ Text Input   │      │
│  │  (Flask)     │  │  (Mic)       │  │  (Chat)      │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Intent     │  │   Entity     │  │   Context    │      │
│  │  Classifier  │  │  Extraction  │  │   Manager    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼──────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI & Data Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  LLM Service │  │ NBA Data     │  │  Knowledge   │      │
│  │(DeepSeek/    │  │   Fetcher    │  │    Base      │      │
│  │  OpenAI)     │  │              │  │   (RAG)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Docker & Docker Compose installed (recommended)
- Or Python 3.11+ with pip

### Option 1: Using Docker Compose (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/LikY13Yxy/nba_voice_assistant.git
cd nba_voice_assistant

# 2. Configure environment variables (optional)
# Edit .env file or set environment variables
export DEEPSEEK_API_KEY="your-api-key"

# 3. Start the service
docker-compose up -d

# 4. Access the application
# Open browser and visit http://localhost:5000
```

### Option 2: Using Docker

```bash
# Build the image
docker build -t nba-assistant .

# Run the container
docker run -d \
  -p 5000:5000 \
  -e DEEPSEEK_API_KEY="your-api-key" \
  --name nba-assistant \
  nba-assistant
```

### Option 3: Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/LikY13Yxy/nba_voice_assistant.git
cd nba_voice_assistant

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
python web_app.py
```

---

## Environment Variables

Create a `.env` file or export these variables:

### LLM Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider: `deepseek`, `openai`, or `ollama` | `deepseek` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | - |
| `DEEPSEEK_MODEL` | DeepSeek model: `deepseek-chat` or `deepseek-reasoner` | `deepseek-chat` |
| `DEEPSEEK_URL` | DeepSeek API endpoint | `https://api.deepseek.com/chat/completions` |
| `OPENAI_API_KEY` | OpenAI-compatible API key | - |
| `OPENAI_MODEL` | Model name for OpenAI-compatible API | `deepseek-ai/DeepSeek-V3` |
| `OPENAI_BASE_URL` | Base URL for OpenAI-compatible API | `https://api.siliconflow.cn/v1` |
| `OLLAMA_URL` | Ollama local server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5:latest` |

### NBA Data Configuration
| Variable | Description |
|----------|-------------|
| `NBA_API_KEY` | NBA API key (optional) |
| `BALLDONTLIE_API_KEY` | BallDontLie API key (optional) |

---

## Project Structure

```
nba_voice_assistant/
├── modules/                      # Core modules
│   ├── llm.py                   # LLM integration (DeepSeek/OpenAI/Ollama)
│   ├── nba_live_data.py         # NBA data fetching from APIs
│   ├── voice.py                 # Voice processing (STT & TTS)
│   ├── knowledge_base.py        # RAG knowledge base
│   └── data_provider.py         # Data provider utilities
│
├── config.py                    # Configuration management
├── web_app.py                   # Flask web application
├── smart_assistant.py           # CLI version of assistant
├── requirements.txt             # Python dependencies
│
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Docker Compose configuration
├── .dockerignore               # Docker ignore rules
├── .gitignore                  # Git ignore rules
│
├── data/                       # Data storage
│   └── knowledge_base.json     # NBA knowledge base
│
└── README.md                   # Documentation
```

---

## Usage

### Web Interface

1. **Access the application**
   - Open browser and navigate to `http://localhost:5000`

2. **Text Input**
   - Type your NBA-related questions in the chat box
   - Press Enter or click Send button

3. **Voice Input**
   - Click the microphone button
   - Speak your question clearly
   - The assistant will process and respond

4. **View Responses**
   - Text response appears in chat
   - Voice response plays automatically (if enabled)

### Example Queries

| Category | Example Queries |
|----------|-----------------|
| **Player Stats** | "What's LeBron James' stats this season?"<br>"Show me Stephen Curry's shooting percentage" |
| **Team Info** | "What's the current NBA standings?"<br>"Show me Lakers' recent games" |
| **Game Schedule** | "What games are playing today?"<br>"When is the next Warriors game?" |
| **Player Comparison** | "Compare Kevin Durant and Giannis Antetokounmpo"<br>"Who's better: Curry or LeBron?" |
| **NBA Knowledge** | "Tell me about the history of the Lakers"<br>"What are the NBA playoff rules?" |

---

## APIs & Data Sources

### LLM Providers
- **DeepSeek API**: Primary provider for intelligent dialogue
- **OpenAI API**: Alternative provider (SiliconFlow compatible)
- **Ollama**: Local LLM deployment for offline usage

### NBA Data Sources
- **NBA API**: Official NBA statistics (requires API key)
- **BallDontLie API**: Free NBA statistics API
- **nba_api**: Python library for NBA.com data

### Voice Services
- **SpeechRecognition**: Google Speech Recognition API
- **Edge-TTS**: Microsoft Edge Text-to-Speech

---

## Docker Commands

```bash
# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart service
docker-compose restart

# Rebuild and start
docker-compose up -d --build

# View running containers
docker ps

# Access container shell
docker exec -it nba-voice-assistant /bin/bash
```

---

## Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows with WSL
- **Python**: 3.11 or higher (for manual installation)
- **Docker**: 20.10+ (for containerized deployment)
- **Memory**: 2GB RAM minimum
- **Network**: Internet connection for API calls

### Optional Requirements
- **Microphone**: For voice input functionality
- **Speakers**: For voice output functionality

---

## License

This project is created for educational purposes as part of a Natural Language Processing course.

## Author

GitHub: [@LikY13Yxy](https://github.com/LikY13Yxy)

---

## Acknowledgments

- DeepSeek for providing the LLM API
- NBA.com and BallDontLie for NBA data
- Flask community for the web framework
