"""
Configuration file for Voice Agent STS (Speech-to-Speech)
Uses GPT-4o Realtime API for direct audio-to-audio processing
Supports both OpenAI and Azure OpenAI
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# Provider Selection: Set USE_AZURE=true in .env to use Azure OpenAI
# =============================================================================
USE_AZURE = os.getenv("USE_AZURE", "false").lower() == "true"

# =============================================================================
# OpenAI Configuration (used when USE_AZURE=false)
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REALTIME_MODEL = "gpt-4o-realtime-preview-2024-12-17"
REALTIME_WS_URL = "wss://api.openai.com/v1/realtime"

# =============================================================================
# Azure OpenAI Configuration (used when USE_AZURE=true)
# =============================================================================
# Strip quotes from environment variables (Azure Container Apps sometimes adds them)
def _strip_quotes(value):
    if value:
        return value.strip('"\'')
    return value

AZURE_OPENAI_ENDPOINT = _strip_quotes(os.getenv("AZURE_OPENAI_ENDPOINT"))  # e.g., https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY = _strip_quotes(os.getenv("AZURE_OPENAI_API_KEY"))
AZURE_OPENAI_DEPLOYMENT = _strip_quotes(os.getenv("AZURE_OPENAI_DEPLOYMENT"))  # Your deployment name
AZURE_API_VERSION = _strip_quotes(os.getenv("AZURE_API_VERSION", "2024-10-01-preview"))

# Audio Settings (GPT-4o Realtime API uses 24kHz PCM16)
SAMPLE_RATE = 24000  # 24kHz required by GPT-4o Realtime API
AUDIO_FORMAT = "pcm16"
CHANNELS = 1

# Voice Settings
VOICE = "alloy"  # Options: alloy, echo, shimmer, ash, ballad, coral, sage, verse
VOICE_SPEED = 1.0

# Session Settings
SYSTEM_PROMPT = """You are a helpful voice assistant. Keep your responses concise and natural 
for voice conversation, ideally 1-3 sentences unless more detail is specifically requested. 
Speak in a friendly, conversational tone."""

# Turn Detection (Server VAD)
# Threshold: 0.0-1.0 (higher = less sensitive, ignores quiet sounds)
# - 0.3-0.5: Sensitive (picks up quiet speech, but also background noise)
# - 0.6-0.7: Balanced (good for most environments)
# - 0.8-0.9: Strict (requires clear, loud speech)
TURN_DETECTION_TYPE = "server_vad"  # or "none" for manual
TURN_DETECTION_THRESHOLD = 0.7  # Increased to ignore background noise
TURN_DETECTION_PREFIX_PADDING_MS = 200  # Reduced to avoid capturing noise before speech
TURN_DETECTION_SILENCE_DURATION_MS = 700  # Increased to wait longer before responding

# Performance Settings
AUDIO_CHUNK_SIZE = 8192
AUDIO_QUEUE_MAXSIZE = 500

# Server Settings
# Use 0.0.0.0 for Docker, localhost for local development
# Both HTTP and WebSocket use the same port (8080) for Azure Container Apps compatibility
HOST = os.getenv("HOST", "localhost")
PORT = int(os.getenv("PORT", "8080"))  # Single port for both HTTP and WebSocket
HTTP_PORT = PORT
WS_PORT = PORT

# Recording Settings
# Set ENABLE_RECORDINGS=true in .env to save audio recordings
ENABLE_RECORDINGS = os.getenv("ENABLE_RECORDINGS", "false").lower() == "true"

# Debug Settings
DEBUG = True
VERBOSE = False

# Validate API keys
def validate_config():
    """Validate that required API keys are set"""
    errors = []
    
    if USE_AZURE:
        # Azure OpenAI validation
        if not AZURE_OPENAI_ENDPOINT:
            errors.append("AZURE_OPENAI_ENDPOINT not set")
        if not AZURE_OPENAI_API_KEY:
            errors.append("AZURE_OPENAI_API_KEY not set")
        if not AZURE_OPENAI_DEPLOYMENT:
            errors.append("AZURE_OPENAI_DEPLOYMENT not set")
        
        if not errors:
            print(f"✓ Using Azure OpenAI")
            print(f"  Endpoint: {AZURE_OPENAI_ENDPOINT}")
            print(f"  Deployment: {AZURE_OPENAI_DEPLOYMENT}")
            print(f"  API Version: {AZURE_API_VERSION}")
    else:
        # OpenAI validation
        if not OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY not set")
        
        if not errors:
            print(f"✓ Using OpenAI")
            print(f"  Model: {REALTIME_MODEL}")
    
    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    if VERBOSE:
        print("✓ Configuration validated")

if __name__ == "__main__":
    validate_config()
    print("✓ All required API keys are configured")

