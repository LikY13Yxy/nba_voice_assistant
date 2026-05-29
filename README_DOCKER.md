# NBA语音助手 - Docker 部署指南

## 快速开始

### 方式一：使用 Docker Compose（推荐）

1. **克隆项目**
```bash
git clone <你的GitHub仓库地址>
cd nba_voice_assistant_v2
```

2. **配置环境变量（可选）**
创建 `.env` 文件来配置 API 密钥：
```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问应用**
打开浏览器访问：http://localhost:5000

### 方式二：使用 Docker 命令

1. **构建镜像**
```bash
docker build -t nba-assistant .
```

2. **运行容器**
```bash
docker run -d \
  -p 5000:5000 \
  -e DEEPSEEK_API_KEY=你的API密钥 \
  --name nba-assistant \
  nba-assistant
```

## 环境变量配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `LLM_PROVIDER` | LLM提供商 | `deepseek` |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | - |
| `DEEPSEEK_MODEL` | DeepSeek模型 | `deepseek-chat` |
| `OPENAI_API_KEY` | OpenAI兼容API密钥 | - |
| `OPENAI_BASE_URL` | OpenAI兼容API地址 | - |
| `NBA_API_KEY` | NBA API密钥 | - |
| `BALLDONTLIE_API_KEY` | BallDontLie API密钥 | - |

## 常用命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up -d --build

# 查看容器状态
docker ps
```

## 注意事项

1. **API 密钥**：请确保在运行前配置好必要的 API 密钥
2. **端口占用**：确保 5000 端口未被其他程序占用
3. **网络**：容器需要访问外网以调用 API 服务

## 故障排除

### 容器无法启动
```bash
# 查看详细日志
docker-compose logs
```

### 端口被占用
修改 `docker-compose.yml` 中的端口映射：
```yaml
ports:
  - "8080:5000"  # 将主机8080端口映射到容器5000端口
```
