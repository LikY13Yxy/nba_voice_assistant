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
- [Docker Deployment](#docker-deployment)
- [Requirements](#requirements)

---

## Features

### Core Capabilities
- **Voice Interaction**: Natural voice conversations with speech recognition and text-to-speech
- **Real-time NBA Data**: Query player stats, team standings, game schedules, and league leaders
- **Offline Local Answers**: SQLite-based local database for answering queries without API calls
- **Intelligent Dialogue**: AI-powered conversations using state-of-the-art LLMs
- **Player Comparison**: Compare statistics between multiple players
- **Knowledge Base**: RAG (Retrieval-Augmented Generation) for NBA history and rules
- **Player Aliases**: Supports Chinese nicknames (e.g. "老詹" → 詹姆斯, "华子" → 爱德华兹)

### User Interfaces
- **Web Interface**: Clean, responsive web UI with streaming responses built with Flask
- **CLI Interface**: Command-line text/voice mode via `smart_assistant.py`
- **Voice Input**: Microphone support for hands-free interaction
- **Voice Output**: TTS playback with toggle control

---

## Tech Stack

### Backend Framework
| Technology | Purpose | Version |
|------------|---------|---------|
| **Flask** | Web framework for REST API and web interface | >=3.0.0 |
| **Python** | Programming language | 3.11+ |
| **SQLite** | Local database for offline NBA data | built-in |

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
| **ESPN API** | Free NBA statistics (no key required) |
| **TheSportsDB** | Free sports data API (no key required) |
| **BallDontLie API** | Free NBA statistics API |
| **nba_api** | Python wrapper for NBA.com API (>=1.4.1) |
| **Local SQLite DB** | Offline fallback with pre-loaded NBA data |

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
│  │   Web UI     │  │ Voice Input  │  │  CLI Mode    │      │
│  │  (Flask)     │  │  (Mic)       │  │ (Terminal)   │      │
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
│  │  LLM Service │  │ NBA Data     │  │  Local DB    │      │
│  │(DeepSeek/    │  │   Fetcher    │  │  (SQLite)    │      │
│  │  OpenAI)     │  │ (Multi-API)  │  │  + RAG       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites
- Python 3.11+ with pip
- (Optional) Docker & Docker Compose for containerized deployment

### Option 1: Manual Installation (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/LikY13Yxy/nba_voice_assistant.git
cd nba_voice_assistant

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edit .env and set your DEEPSEEK_API_KEY

# 5. Run the web application
python web_app.py

# Or run the CLI assistant
python smart_assistant.py
```

### Option 2: Using Docker Compose

```bash
# 1. Clone the repository
git clone https://github.com/LikY13Yxy/nba_voice_assistant.git
cd nba_voice_assistant

# 2. Configure environment variables
export DEEPSEEK_API_KEY="your-api-key"

# 3. Start the service
docker-compose up -d

# 4. Access the application
# Open browser and visit http://localhost:5000
```

### Option 3: Using Docker

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

---

## Environment Variables

Create a `.env` file (copy from `.env.example`) or export these variables:

### LLM Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider: `deepseek`, `openai`, or `ollama` | `deepseek` |
| `DEEPSEEK_API_KEY` | DeepSeek API key (**required**) | - |
| `DEEPSEEK_MODEL` | DeepSeek model: `deepseek-chat` or `deepseek-reasoner` | `deepseek-chat` |
| `DEEPSEEK_URL` | DeepSeek API endpoint | `https://api.deepseek.com/chat/completions` |
| `OPENAI_API_KEY` | OpenAI-compatible API key | - |
| `OPENAI_MODEL` | Model name for OpenAI-compatible API | `deepseek-ai/DeepSeek-V3` |
| `OPENAI_BASE_URL` | Base URL for OpenAI-compatible API | `https://api.siliconflow.cn/v1` |
| `OLLAMA_URL` | Ollama local server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name | `qwen2.5:latest` |

### NBA Data Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `USE_LIVE_DATA` | Enable real-time NBA data fetching | `true` |
| `NBA_API_KEY` | RapidAPI NBA API key (optional) | - |
| `BALLDONTLIE_API_KEY` | BallDontLie API key (optional) | - |

> **Note**: ESPN API and TheSportsDB work without API keys. The local SQLite database serves as an offline fallback when no API is available.

---

## Project Structure

```
nba_voice_assistant/
├── modules/                      # Core modules
│   ├── llm.py                   # LLM integration (DeepSeek/OpenAI/Ollama)
│   ├── nba_live_data.py         # NBA real-time data fetching with cache
│   ├── data_provider.py         # Multi-source data provider (ESPN/BallDontLie/etc.)
│   ├── local_answer.py          # Local intelligent answer engine
│   ├── local_database.py        # SQLite database initialization & queries
│   ├── knowledge_base.py        # RAG knowledge base
│   ├── voice.py                 # Voice processing (STT & TTS)
│   ├── nba_data.py              # Static fallback data
│   └── data/
│       └── nba_local.db         # SQLite database (auto-generated)
│
├── data/                        # Data storage
│   └── knowledge_base.json     # RAG knowledge base data
│
├── config.py                    # Configuration & player/team aliases
├── web_app.py                   # Flask web application
├── smart_assistant.py           # CLI assistant (text/voice mode)
├── update_local_data.py         # Script to update local database from APIs
├── requirements.txt             # Python dependencies
│
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Docker Compose configuration
├── .dockerignore                # Docker ignore rules
├── .gitignore                   # Git ignore rules
├── .env.example                 # Environment variable template
│
└── README.md                    # Documentation
```

---

## Usage

### Web Interface

1. **Start the application**
   ```bash
   python web_app.py
   ```

2. **Access the application**
   - Open browser and navigate to `http://localhost:8081`

3. **Text Input**
   - Type your NBA-related questions in the chat box
   - Press Enter or click Send button

4. **Voice Input**
   - Click the microphone button
   - Speak your question clearly
   - The assistant will process and respond

5. **Voice Output**
   - Toggle voice playback with the speaker button
   - Responses will be read aloud when enabled

### CLI Assistant

```bash
python smart_assistant.py
```

Choose between:
- **Voice mode** (1): Speak questions, hear spoken responses
- **Text mode** (2): Type questions, read text responses

### Update Local Database

```bash
python update_local_data.py
```

Fetches latest NBA data from ESPN and updates the local SQLite database.

### Example Queries

| Category | Example Queries |
|----------|-----------------|
| **Player Stats** | "詹姆斯数据" / "LeBron James' stats" |
| **Team Info** | "NBA排名" / "湖人几个冠军" |
| **Game Schedule** | "今天有哪些比赛" / "湖人赛程" |
| **Player Comparison** | "詹姆斯和库里谁更强" / "Compare KD and Giannis" |
| **NBA Knowledge** | "2024年NBA冠军" / "得分王是谁" |
| **Player Details** | "约基奇身高" / "库里什么位置" / "字母哥体重" |

---

## APIs & Data Sources

### LLM Providers
- **DeepSeek API**: Primary provider for intelligent dialogue
- **OpenAI API**: Alternative provider (SiliconFlow compatible)
- **Ollama**: Local LLM deployment for offline usage

### NBA Data Sources (with fallback chain)
1. **ESPN API** — Free, no API key required (primary)
2. **TheSportsDB** — Free, no API key required
3. **nba_api** — Python library for NBA.com data
4. **BallDontLie API** — Free NBA statistics API
5. **Local SQLite Database** — Offline fallback with pre-loaded data

### Voice Services
- **SpeechRecognition**: Google Speech Recognition API (Chinese supported)
- **Edge-TTS**: Microsoft Edge Text-to-Speech (zh-CN-XiaoxiaoNeural)

---

## Docker Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Rebuild and restart
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
- **Network**: Internet connection for API calls (optional if using local DB only)

### Optional Requirements
- **Microphone**: For voice input functionality
- **Speakers**: For voice output functionality
- **nba_api**: For real-time NBA statistics (`pip install nba_api`)

---

## License

This project is created for educational purposes as part of a Natural Language Processing course.

## Author

GitHub: [@LikY13Yxy](https://github.com/LikY13Yxy)

---

## Acknowledgments

- DeepSeek for providing the LLM API
- ESPN and TheSportsDB for free NBA data APIs
- NBA.com and BallDontLie for NBA data
- Flask community for the web framework
