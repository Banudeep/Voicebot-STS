# 🎙️ STS Voice Agent

<div align="center">

**Speech-to-Speech Voice Agent powered by GPT-4o Realtime API**

_Direct audio-to-audio processing with zero intermediate text conversion_

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](Dockerfile)

</div>

---

## 🌟 What This App Does

The **STS Voice Agent** is a real-time voice assistant that enables natural, conversational interactions through direct speech-to-speech processing. Unlike traditional voice agents that convert speech → text → text → speech, this agent processes audio directly, resulting in:

- ⚡ **Ultra-low latency** conversations
- 🎯 **Natural interruptions** (barge-in support)
- 🔊 **High-quality audio** at 24kHz
- 🌐 **Cloud-ready** with Docker and Azure Container Apps support
- 🔧 **Fully configurable** voice sensitivity and behavior

---

## ✨ Key Features

### 🎤 **Direct Speech-to-Speech Processing**

- **No separate STT/TTS services** - GPT-4o Realtime handles everything
- **Single API call** for complete audio processing
- **24kHz PCM16 audio** for high-quality voice interactions

### 🧠 **Intelligent Voice Activity Detection**

- **Server-side VAD** powered by OpenAI
- **Real-time sensitivity adjustment** via UI slider
- **Configurable silence detection** and turn-taking

### 💬 **Natural Conversation Flow**

- **Full-duplex communication** - always listening, even while speaking
- **Interruption support** - users can interrupt AI mid-response
- **Live transcription** of both user and AI speech
- **Streaming responses** for immediate feedback

### 🎨 **Modern Web Interface**

- **Beautiful, responsive UI** with real-time status indicators
- **Live audio visualizer** during speech
- **Chat history** with user and AI messages
- **Settings panel** for real-time configuration

### ☁️ **Production-Ready Deployment**

- **Docker support** with optimized image
- **Azure Container Apps** compatible
- **Azure OpenAI** integration
- **Environment-based configuration**

### 🔧 **Advanced Configuration**

- **Multiple voice options** (alloy, echo, shimmer, ash, ballad, coral, sage, verse)
- **Customizable system prompts**
- **Adjustable VAD thresholds**
- **Optional audio recording** for debugging

---

## 🏗️ Architecture

```
┌─────────────────┐     WebSocket      ┌─────────────────┐     WebSocket      ┌─────────────────┐
│                 │ ◄───────────────► │                 │ ◄───────────────► │                 │
│     Browser     │   Audio (24kHz)   │   STS Agent     │   Audio (24kHz)    │  GPT-4o Realtime│
│   (Web UI)      │   PCM16 mono      │    (Python)     │   PCM16 mono       │      API        │
│                 │   Port: 8080      │                 │                   │                 │
└─────────────────┘                    └─────────────────┘                    └─────────────────┘
         │                                       │                                       │
         │                                       │                                       │
    AudioWorklet                          aiohttp Server                        OpenAI/Azure
    (24kHz capture)                       (Unified HTTP+WS)                      Realtime API
```

### **Technology Stack**

- **Backend**: Python 3.11+ with asyncio
- **Web Server**: aiohttp (unified HTTP + WebSocket on port 8080)
- **Audio Processing**: AudioWorklet API (browser-side)
- **AI Provider**: GPT-4o Realtime API (OpenAI or Azure OpenAI)
- **Deployment**: Docker + Azure Container Apps

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- OpenAI API key with GPT-4o Realtime access **OR** Azure OpenAI resource
- Modern web browser with WebRTC support

### Local Installation

1. **Clone and navigate to the project:**

   ```bash
   cd voice_agent_sts
   ```

2. **Create virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**

   Create a `.env` file:

   ```env
   # For OpenAI
   OPENAI_API_KEY=your-openai-api-key-here

   # OR for Azure OpenAI
   USE_AZURE=true
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
   AZURE_OPENAI_API_KEY=your-azure-api-key
   AZURE_OPENAI_DEPLOYMENT=your-deployment-name
   AZURE_API_VERSION=2024-10-01-preview

   # Optional settings
   ENABLE_RECORDINGS=false  # Set to true to save audio recordings
   ```

5. **Run the server:**

   ```bash
   python sts_agent.py
   ```

6. **Open in browser:**
   ```
   http://localhost:8080
   ```

---

## 🐳 Docker Deployment

### Build and Run Locally

```bash
# Build the image
docker build -t sts-voice-agent .

# Run with OpenAI
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your-key \
  sts-voice-agent

# Run with Azure OpenAI
docker run -p 8080:8080 \
  -e USE_AZURE=true \
  -e AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com \
  -e AZURE_OPENAI_API_KEY=your-key \
  -e AZURE_OPENAI_DEPLOYMENT=your-deployment \
  sts-voice-agent
```

### Docker Compose

```bash
# Create .env file with your credentials, then:
docker-compose up --build
```

### Push to Docker Hub

```bash
docker build -t YOUR_USERNAME/sts-voice-agent:latest .
docker push YOUR_USERNAME/sts-voice-agent:latest
```

---

## ⚙️ Configuration

### Environment Variables

| Variable                  | Description                    | Required                                            |
| ------------------------- | ------------------------------ | --------------------------------------------------- |
| `USE_AZURE`               | Set to `true` for Azure OpenAI | No (default: `false`)                               |
| `OPENAI_API_KEY`          | OpenAI API key                 | Yes (if `USE_AZURE=false`)                          |
| `AZURE_OPENAI_ENDPOINT`   | Azure OpenAI endpoint URL      | Yes (if `USE_AZURE=true`)                           |
| `AZURE_OPENAI_API_KEY`    | Azure OpenAI API key           | Yes (if `USE_AZURE=true`)                           |
| `AZURE_OPENAI_DEPLOYMENT` | Azure deployment name          | Yes (if `USE_AZURE=true`)                           |
| `AZURE_API_VERSION`       | Azure API version              | No (default: `2024-10-01-preview`)                  |
| `ENABLE_RECORDINGS`       | Save audio recordings          | No (default: `false`)                               |
| `HOST`                    | Server host                    | No (default: `localhost`, use `0.0.0.0` for Docker) |
| `PORT`                    | Server port                    | No (default: `8080`)                                |

### Config File (`config.py`)

Customize behavior by editing `config.py`:

```python
# Voice selection (8 options available)
VOICE = "alloy"  # Options: alloy, echo, shimmer, ash, ballad, coral, sage, verse

# System prompt
SYSTEM_PROMPT = """You are a helpful voice assistant..."""

# Voice Activity Detection
TURN_DETECTION_THRESHOLD = 0.7  # 0.0-1.0 (higher = less sensitive)
TURN_DETECTION_SILENCE_DURATION_MS = 700  # Wait time before responding
```

---

## 🎯 Features in Detail

### 1. **Real-Time Audio Processing**

- **24kHz sample rate** for high-quality audio
- **20ms frame size** (480 samples) for low latency
- **PCM16 format** (16-bit signed integer)
- **Mono channel** for optimal processing

### 2. **Smart Voice Detection**

- **Server-side VAD** eliminates client-side processing overhead
- **Adjustable sensitivity** via UI slider (0.3-0.95)
- **Hysteresis-based detection** prevents false triggers
- **Prefix padding** captures speech start accurately

### 3. **Natural Conversation**

- **Full-duplex** - always listening, even while AI speaks
- **Barge-in support** - interrupt AI mid-sentence
- **Turn-taking** - automatic detection of speech completion
- **Context preservation** - maintains conversation history

### 4. **Live Transcription**

- **Real-time user speech** transcription (optional)
- **AI response** transcription displayed in chat
- **Streaming updates** as AI generates response
- **English-only** (configurable)

### 5. **Web Interface Features**

- **Connection status** indicators
- **Live audio visualizer** during speech
- **Chat history** with user and AI messages
- **Settings panel** for real-time adjustments
- **Responsive design** works on desktop and mobile

### 6. **Production Features**

- **Error handling** with throttled logging
- **Connection management** (auto-reconnect)
- **Audio recording** (optional, for debugging)
- **Health checks** for container orchestration
- **Unified port** (8080) for HTTP and WebSocket

---

## 📊 Comparison: STS vs Traditional Voice Agents

| Feature              | Traditional Voice Agent      | STS Voice Agent     |
| -------------------- | ---------------------------- | ------------------- |
| **Architecture**     | STT → LLM → TTS (3 services) | Single Realtime API |
| **Latency**          | ~500-1000ms                  | ~100-300ms          |
| **API Calls**        | 3 per interaction            | 1 per interaction   |
| **Interruptions**    | Limited                      | Full support        |
| **Audio Quality**    | 16kHz (typical)              | 24kHz               |
| **VAD**              | Client-side                  | Server-side         |
| **Setup Complexity** | High (3 services)            | Low (1 service)     |
| **Cost**             | 3x API calls                 | 1x API call         |

---

## 🔧 Advanced Usage

### Real-Time Sensitivity Adjustment

Use the **⚙️ Settings** button in the UI to adjust voice detection sensitivity:

- **Very Sensitive (0.3-0.4)**: Picks up quiet speech, but also background noise
- **Sensitive (0.45-0.55)**: Good for quiet environments
- **Balanced (0.6-0.7)**: Default - works for most cases
- **Strict (0.75-0.85)**: Requires clear, direct speech
- **Very Strict (0.9-0.95)**: Only responds to loud, clear voice

### Audio Recording

Enable recordings for debugging:

```env
ENABLE_RECORDINGS=true
```

Recordings are saved to `recordings/` directory as WAV files with timestamps.

### Custom Voice Selection

Edit `config.py` to change the AI voice:

```python
VOICE = "alloy"  # Change to: echo, shimmer, ash, ballad, coral, sage, or verse
```

### Custom System Prompt

Personalize the AI's behavior:

```python
SYSTEM_PROMPT = """You are a friendly customer service assistant.
Always be polite and helpful. Keep responses under 2 sentences."""
```

---

## 🌐 Azure Container Apps Deployment

### Prerequisites

- Azure Container Apps environment
- Docker Hub account (or Azure Container Registry)
- Azure OpenAI resource (if using Azure)

### Deployment Steps

1. **Build and push to Docker Hub:**

   ```bash
   docker build -t YOUR_USERNAME/sts-voice-agent:latest .
   docker push YOUR_USERNAME/sts-voice-agent:latest
   ```

2. **In Azure Container Apps:**

   - Create new revision
   - Set image: `YOUR_USERNAME/sts-voice-agent:latest`
   - Configure environment variables
   - Set **Target port: 8080** in Ingress settings
   - Deploy

3. **The app will be accessible at:**
   ```
   https://your-app.azurecontainerapps.io
   ```

### Environment Variables in Azure

Set these in Container Apps → Environment Variables:

```
USE_AZURE=true
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-key
AZURE_OPENAI_DEPLOYMENT=your-deployment
PORT=8080
HOST=0.0.0.0
```

---

## 🐛 Troubleshooting

### Connection Issues

**"Failed to connect to OpenAI Realtime API"**

- ✅ Verify API key is correct
- ✅ Check network connectivity
- ✅ Ensure you have GPT-4o Realtime API access
- ✅ For Azure: Verify endpoint, deployment name, and API key

**"Connection timeout"**

- ✅ Check firewall settings
- ✅ Verify endpoint URL is correct
- ✅ Ensure Azure OpenAI resource is accessible

### Audio Issues

**No audio playback**

- ✅ Check browser console for errors
- ✅ Verify microphone permissions
- ✅ Try refreshing the page
- ✅ Check browser audio settings

**Audio not being captured**

- ✅ Grant microphone permissions
- ✅ Check browser console for errors
- ✅ Verify AudioWorklet is loading (`audio-processor.js`)
- ✅ Try a different browser

**Background noise triggering responses**

- ✅ Increase sensitivity threshold in UI (Settings → Sensitivity)
- ✅ Use headphones to prevent echo
- ✅ Adjust `TURN_DETECTION_THRESHOLD` in `config.py`

### Performance Issues

**High latency**

- ✅ Check network connection speed
- ✅ Verify you're using a supported region
- ✅ Reduce other network traffic
- ✅ Check Azure OpenAI resource location

**Too many error messages**

- ✅ Error throttling is enabled (1 per second max)
- ✅ Check connection stability
- ✅ Verify API credentials

---

## 📁 Project Structure

```
voice_agent_sts/
├── sts_agent.py          # Main server application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker build instructions
├── docker-compose.yml    # Docker Compose configuration
├── .dockerignore         # Docker ignore patterns
├── README.md             # This file
├── __init__.py           # Package initialization
├── recordings/          # Audio recordings (if enabled)
└── web_ui/
    ├── sts_agent.html    # Web interface
    └── audio-processor.js # AudioWorklet processor
```

---

## 🔐 Security Notes

- **API Keys**: Never commit `.env` files or expose API keys
- **HTTPS**: Use HTTPS in production (Azure Container Apps provides this)
- **CORS**: Currently configured for localhost (adjust for production)
- **WebSocket**: Uses WSS (secure WebSocket) when served over HTTPS

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🙏 Acknowledgments

- **OpenAI** for the GPT-4o Realtime API
- **Azure** for container hosting capabilities
- Built with ❤️ using Python, aiohttp, and modern web technologies

---

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

<div align="center">

**Made with ❤️ for natural voice interactions**

[⭐ Star this repo](https://github.com/yourusername/voice-agent-sts) if you find it useful!

</div>
