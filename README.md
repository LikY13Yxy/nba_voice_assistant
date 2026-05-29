# NBA Voice Assistant

An intelligent NBA voice assistant powered by LLM, featuring voice interaction, real-time NBA data queries, and intelligent dialogue capabilities.

## Features

- **Voice Interaction**: Supports speech recognition and text-to-speech for natural voice conversations
- **Real-time NBA Data**: Query player stats, team standings, game schedules, and more
- **Intelligent Dialogue**: Powered by LLM (DeepSeek/OpenAI) for professional NBA knowledge Q&A
- **Web Interface**: Clean and intuitive web UI for easy interaction
- **Docker Support**: One-click deployment with Docker for consistent environment

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/LikY13Yxy/nba_voice_assistant.git
cd nba_voice_assistant

# Start the service
docker-compose up -d

# Access the application
# Open browser and visit http://localhost:5000
```

### Using Docker

```bash
# Build the image
docker build -t nba-assistant .

# Run the container
docker run -d -p 5000:5000 --name nba-assistant nba-assistant
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/LikY13Yxy/nba_voice_assistant.git
cd nba_voice_assistant

# Install dependencies
pip install -r requirements.txt

# Run the application
python web_app.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider (deepseek/openai/ollama) | `deepseek` |
| `DEEPSEEK_API_KEY` | DeepSeek API key | - |
| `DEEPSEEK_MODEL` | DeepSeek model name | `deepseek-chat` |
| `OPENAI_API_KEY` | OpenAI-compatible API key | - |
| `OPENAI_BASE_URL` | OpenAI-compatible base URL | - |
| `NBA_API_KEY` | NBA API key | - |
| `BALLDONTLIE_API_KEY` | BallDontLie API key | - |

## Project Structure

```
nba_voice_assistant/
├── modules/
│   ├── llm.py              # LLM integration
│   ├── nba_live_data.py    # NBA data fetching
│   ├── voice.py            # Voice processing
│   ├── knowledge_base.py   # Knowledge base
│   └── data_provider.py    # Data provider
├── config.py               # Configuration
├── web_app.py              # Web application
├── smart_assistant.py      # CLI assistant
├── requirements.txt        # Dependencies
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── README.md               # Documentation
```

## Usage

### Web Interface

1. Access `http://localhost:5000` in your browser
2. Type your NBA-related questions in the chat box
3. Or click the microphone button for voice input
4. The assistant will respond with voice and text

### Example Queries

- "What's LeBron James' stats this season?"
- "Show me the current NBA standings"
- "What games are playing today?"
- "Compare Stephen Curry and Kevin Durant"
- "Tell me about the history of the Lakers"

## API Support

This project uses the following data sources:

- **DeepSeek API**: Intelligent dialogue and analysis
- **NBA API**: Real-time NBA data
- **BallDontLie API**: Free NBA statistics (fallback)

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
```

## Requirements

- Python 3.11+
- Docker & Docker Compose (optional)
- API keys for LLM providers

## License

This project is for educational purposes.

## Author

Created for Natural Language Processing course project.
