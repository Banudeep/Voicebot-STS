"""
Speech-to-Speech Voice Agent using GPT-4o Realtime API
No separate STT/TTS needed - direct audio-to-audio processing
"""
import asyncio
import json
import base64
import wave
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from aiohttp import web
from aiohttp.web_ws import WebSocketResponse
import websockets
from websockets.exceptions import ConnectionClosed

import config


class STSVoiceAgent:
    """Voice agent using GPT-4o Realtime API for Speech-to-Speech"""
    
    def __init__(self):
        self.active_connections = set()
        self.openai_ws = None
        self.session_configured = False
        
        # Audio recording storage (only if enabled)
        self.audio_recordings = {}
        if config.ENABLE_RECORDINGS:
            self.recordings_dir = Path(__file__).parent / "recordings"
            self.recordings_dir.mkdir(exist_ok=True)
        else:
            self.recordings_dir = None
        
        # Response tracking
        self.current_response_id = None
        self.is_responding = False
        
        # Error throttling (prevent spam)
        self.last_error_time = 0
        self.error_count = 0
    
    async def _send_ws_message(self, websocket, message):
        """Send message through WebSocket (works with both websockets and aiohttp)"""
        try:
            if hasattr(websocket, 'send_str'):
                # aiohttp WebSocketResponse
                if websocket.closed or (hasattr(websocket, 'closing') and websocket.closing):
                    if config.DEBUG:
                        print(f"⚠️ WebSocket is closed/closing, skipping message")
                    return
                return await websocket.send_str(message)
            else:
                # websockets library
                if websocket.closed:
                    if config.DEBUG:
                        print(f"⚠️ WebSocket is closed, skipping message")
                    return
                return await websocket.send(message)
        except (ConnectionError, OSError, RuntimeError, Exception) as e:
            # WebSocket is closing or closed - ignore
            error_type = type(e).__name__
            if config.DEBUG:
                print(f"⚠️ Could not send message (WebSocket error: {error_type}): {str(e) if str(e) else repr(e)}")
            return
        
    async def initialize(self):
        """Initialize the STS agent"""
        print("Initializing STS Voice Agent...")
        config.validate_config()
        
        if config.ENABLE_RECORDINGS:
            print(f"✓ Recordings enabled (saving to: {self.recordings_dir})")
        else:
            print("ℹ️ Recordings disabled (set ENABLE_RECORDINGS=true to enable)")
        
        print("=" * 60)
        print("STS Voice Agent Ready!")
        print("=" * 60)
    
    async def connect_to_openai(self):
        """Establish WebSocket connection to OpenAI or Azure OpenAI Realtime API"""
        
        if config.USE_AZURE:
            # Azure OpenAI Realtime API
            if not all([config.AZURE_OPENAI_ENDPOINT, config.AZURE_OPENAI_API_KEY, config.AZURE_OPENAI_DEPLOYMENT]):
                raise ValueError(
                    "Azure OpenAI requires AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, "
                    "and AZURE_OPENAI_DEPLOYMENT environment variables"
                )
            
            # Clean up endpoint - remove trailing slashes and convert to wss://
            clean_endpoint = config.AZURE_OPENAI_ENDPOINT.rstrip('/').replace("https://", "wss://").replace("http://", "ws://")
            # Properly encode query parameters
            query_params = urlencode({
                "api-version": config.AZURE_API_VERSION,
                "deployment": config.AZURE_OPENAI_DEPLOYMENT
            })
            url = f"{clean_endpoint}/openai/realtime?{query_params}"
            
            headers = {"api-key": config.AZURE_OPENAI_API_KEY}
            
            print(f"Connecting to Azure OpenAI Realtime:")
            print(f"  Endpoint: {config.AZURE_OPENAI_ENDPOINT}")
            print(f"  Deployment: {config.AZURE_OPENAI_DEPLOYMENT}")
            print(f"  API Version: {config.AZURE_API_VERSION}")
            print(f"  WebSocket URL: {url}")
        else:
            # Standard OpenAI Realtime API
            url = f"{config.REALTIME_WS_URL}?model={config.REALTIME_MODEL}"
            
            headers = {
                "Authorization": f"Bearer {config.OPENAI_API_KEY}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            print(f"Connecting to OpenAI Realtime:")
            print(f"  Model: {config.REALTIME_MODEL}")
            print(f"  WebSocket URL: {url}")
        
        try:
            print(f"Attempting connection (timeout: 30s)...")
            self.openai_ws = await asyncio.wait_for(
                websockets.connect(
                    url,
                    additional_headers=headers,
                    ping_interval=20,
                    ping_timeout=20
                ),
                timeout=30.0
            )
            provider = "Azure OpenAI" if config.USE_AZURE else "OpenAI"
            print(f"✓ Connected to {provider} Realtime API")
            return True
        except asyncio.TimeoutError:
            provider = "Azure OpenAI" if config.USE_AZURE else "OpenAI"
            print(f"❌ Failed to connect to {provider}: Connection timeout after 30 seconds")
            print(f"  URL: {url}")
            return False
        except TypeError as te:
            # Fallback for different websockets versions
            if "additional_headers" in str(te) or "extra_headers" in str(te):
                try:
                    print(f"Attempting connection with extra_headers (timeout: 30s)...")
                    self.openai_ws = await asyncio.wait_for(
                        websockets.connect(
                            url,
                            extra_headers=headers,
                            ping_interval=20,
                            ping_timeout=20
                        ),
                        timeout=30.0
                    )
                    provider = "Azure OpenAI" if config.USE_AZURE else "OpenAI"
                    print(f"✓ Connected to {provider} Realtime API")
                    return True
                except asyncio.TimeoutError:
                    provider = "Azure OpenAI" if config.USE_AZURE else "OpenAI"
                    print(f"❌ Failed to connect to {provider}: Connection timeout after 30 seconds")
                    print(f"  URL: {url}")
                    return False
                except Exception as e2:
                    provider = "Azure OpenAI" if config.USE_AZURE else "OpenAI"
                    error_type = type(e2).__name__
                    error_str = str(e2) if str(e2) else ""
                    error_repr = repr(e2)
                    print(f"❌ Failed to connect to {provider}:")
                    print(f"  Exception Type: {error_type}")
                    print(f"  Error Message: {error_str if error_str else '(empty)'}")
                    print(f"  Error Repr: {error_repr}")
                    print(f"  URL: {url}")
                    import traceback
                    print(f"  Full Traceback:")
                    for line in traceback.format_exc().split('\n'):
                        if line.strip():
                            print(f"    {line}")
                    return False
            else:
                raise
        except Exception as e:
            provider = "Azure OpenAI" if config.USE_AZURE else "OpenAI"
            error_type = type(e).__name__
            error_str = str(e) if str(e) else ""
            error_repr = repr(e)
            print(f"❌ Failed to connect to {provider}:")
            print(f"  Exception Type: {error_type}")
            print(f"  Error Message: {error_str if error_str else '(empty)'}")
            print(f"  Error Repr: {error_repr}")
            print(f"  URL: {url}")
            import traceback
            print(f"  Full Traceback:")
            for line in traceback.format_exc().split('\n'):
                if line.strip():
                    print(f"    {line}")
            return False
    
    async def configure_session(self):
        """Configure the OpenAI Realtime session"""
        if not self.openai_ws:
            return False
        
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": config.SYSTEM_PROMPT,
                "voice": config.VOICE,
                "input_audio_format": config.AUDIO_FORMAT,
                "output_audio_format": config.AUDIO_FORMAT,
                "input_audio_transcription": {
                    "model": "whisper-1",
                    "language": "en"  # Force English transcription
                },
                "turn_detection": {
                    "type": config.TURN_DETECTION_TYPE,
                    "threshold": config.TURN_DETECTION_THRESHOLD,
                    "prefix_padding_ms": config.TURN_DETECTION_PREFIX_PADDING_MS,
                    "silence_duration_ms": config.TURN_DETECTION_SILENCE_DURATION_MS
                }
            }
        }
        
        await self.openai_ws.send(json.dumps(session_config))
        self.session_configured = True
        print("✓ Session configured")
        return True
    
    async def update_vad_threshold(self, threshold: float):
        """Update the VAD threshold in real-time"""
        if not self.openai_ws:
            return
        
        # Clamp threshold to valid range
        threshold = max(0.0, min(1.0, threshold))
        
        update_config = {
            "type": "session.update",
            "session": {
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": threshold,
                    "prefix_padding_ms": config.TURN_DETECTION_PREFIX_PADDING_MS,
                    "silence_duration_ms": config.TURN_DETECTION_SILENCE_DURATION_MS
                }
            }
        }
        
        await self.openai_ws.send(json.dumps(update_config))
        print(f"🎚️ VAD threshold updated to: {threshold}")
    
    async def handle_browser_websocket(self, websocket, path=None):
        """Handle WebSocket connection from browser (works with both websockets and aiohttp)"""
        # Get remote address (works for both libraries)
        try:
            if hasattr(websocket, 'remote_address'):
                remote_addr = websocket.remote_address
            elif hasattr(websocket, 'remote'):
                remote_addr = websocket.remote
            else:
                remote_addr = "unknown"
        except:
            remote_addr = "unknown"
        
        print(f"Browser connected from {remote_addr}")
        
        # Close any existing connections
        if self.active_connections:
            print(f"  Closing {len(self.active_connections)} old connection(s)")
            # Close old OpenAI connection
            if self.openai_ws:
                try:
                    await self.openai_ws.close()
                except:
                    pass
                self.openai_ws = None
            
            for old_ws in list(self.active_connections):
                try:
                    await old_ws.close()
                except:
                    pass
            self.active_connections.clear()
        
        self.active_connections.add(websocket)
        
        # Connect to OpenAI for this session
        if not await self.connect_to_openai():
            await self._send_ws_message(websocket, json.dumps({
                'type': 'error',
                'message': 'Failed to connect to OpenAI Realtime API'
            }))
            return
        
        await self.configure_session()
        
        # Start background task to receive from OpenAI
        openai_task = asyncio.create_task(
            self.receive_from_openai(websocket)
        )
        
        try:
            async for message in websocket:
                try:
                    # Handle both aiohttp WebSocketMessage and websockets string
                    if hasattr(message, 'data'):
                        # aiohttp WebSocketMessage
                        message_str = message.data if isinstance(message.data, str) else message.data.decode('utf-8')
                    else:
                        # websockets library (string)
                        message_str = message
                    
                    data = json.loads(message_str)
                    msg_type = data.get('type')
                    
                    if msg_type == 'session_start':
                        print("📱 Session started")
                        # Send greeting
                        await self.send_greeting()
                    
                    elif msg_type == 'input_audio_buffer.append':
                        # Forward audio to OpenAI
                        audio_base64 = data.get('audio', '')
                        
                        if config.VERBOSE:
                            audio_bytes = base64.b64decode(audio_base64)
                            print(f"📊 Forwarding audio: {len(audio_bytes)} bytes")
                        
                        # Store for recording (if enabled)
                        if config.ENABLE_RECORDINGS:
                            if websocket not in self.audio_recordings:
                                self.audio_recordings[websocket] = []
                            self.audio_recordings[websocket].append(
                                base64.b64decode(audio_base64)
                            )
                        
                        # Forward to OpenAI
                        if self.openai_ws:
                            try:
                                await self.openai_ws.send(json.dumps({
                                    "type": "input_audio_buffer.append",
                                    "audio": audio_base64
                                }))
                            except Exception as e:
                                # Connection might have closed
                                import time
                                current_time = time.time()
                                if current_time - self.last_error_time > 1.0:  # Throttle to once per second
                                    print(f"⚠️ Error sending audio to OpenAI: {type(e).__name__}")
                                    self.last_error_time = current_time
                                    self.error_count = 0
                                self.error_count += 1
                                # If connection is closed, set to None
                                if "closed" in str(e).lower() or "connection" in str(e).lower():
                                    self.openai_ws = None
                        else:
                            # Throttle error messages
                            import time
                            current_time = time.time()
                            if current_time - self.last_error_time > 1.0:
                                print("⚠️ Cannot send audio: OpenAI connection not established")
                                self.last_error_time = current_time
                                self.error_count = 0
                            self.error_count += 1
                    
                    elif msg_type == 'interrupt':
                        # User interrupted - cancel current response
                        if self.is_responding and self.current_response_id and self.openai_ws:
                            await self.openai_ws.send(json.dumps({
                                "type": "response.cancel"
                            }))
                            print("⏹️ Response cancelled by user")
                    
                    elif msg_type == 'text_message':
                        # Direct text input
                        text = data.get('text', '').strip()
                        if text:
                            await self.send_text_message(text)
                    
                    elif msg_type == 'update_sensitivity':
                        # Update VAD threshold
                        threshold = data.get('threshold', 0.7)
                        await self.update_vad_threshold(threshold)
                
                except json.JSONDecodeError:
                    print("⚠️ Invalid JSON received from browser")
                except Exception as e:
                    # Throttle error messages to prevent spam
                    import time
                    current_time = time.time()
                    if current_time - self.last_error_time > 1.0:
                        error_type = type(e).__name__
                        error_msg = str(e) if str(e) else repr(e)
                        print(f"⚠️ Error processing browser message ({error_type}): {error_msg}")
                        self.last_error_time = current_time
                        self.error_count = 0
                    self.error_count += 1
        
        except (ConnectionClosed, ConnectionError, OSError) as e:
            print(f"⚠️ Browser disconnected: {type(e).__name__}")
        except Exception as e:
            print(f"❌ Browser WebSocket error: {e}")
        finally:
            openai_task.cancel()
            
            # Save recording (if enabled)
            if config.ENABLE_RECORDINGS and websocket in self.audio_recordings:
                await self.save_recording(websocket)
            
            # Close OpenAI connection
            if self.openai_ws:
                await self.openai_ws.close()
                self.openai_ws = None
            
            self.active_connections.discard(websocket)
            self.session_configured = False
    
    async def receive_from_openai(self, browser_ws):
        """Receive events from OpenAI and forward to browser"""
        if not self.openai_ws:
            print("⚠️ Cannot receive from OpenAI: connection not established")
            return
        
        try:
            async for message in self.openai_ws:
                try:
                    event = json.loads(message)
                    event_type = event.get('type', '')
                    
                    if config.DEBUG and event_type not in ['response.audio.delta']:
                        print(f"📨 OpenAI event: {event_type}")
                    
                    # Handle different event types
                    if event_type == 'session.created':
                        print("✓ OpenAI session created")
                    
                    elif event_type == 'session.updated':
                        print("✓ OpenAI session updated")
                    
                    elif event_type == 'input_audio_buffer.speech_started':
                        # User started speaking - notify browser
                        await self._send_ws_message(browser_ws, json.dumps({
                            'type': 'speech_started'
                        }))
                        if config.DEBUG:
                            print("🎤 Speech detected")
                    
                    elif event_type == 'input_audio_buffer.speech_stopped':
                        # User stopped speaking
                        await self._send_ws_message(browser_ws, json.dumps({
                            'type': 'speech_stopped'
                        }))
                        if config.DEBUG:
                            print("🔇 Speech ended")
                    
                    elif event_type == 'input_audio_buffer.committed':
                        if config.DEBUG:
                            print("✓ Audio buffer committed")
                    
                    elif event_type == 'conversation.item.input_audio_transcription.completed':
                        # Transcription of user's speech
                        transcript = event.get('transcript', '')
                        if transcript:
                            await self._send_ws_message(browser_ws, json.dumps({
                                'type': 'transcript',
                                'text': transcript
                            }))
                            if config.DEBUG:
                                print(f"📝 User said: {transcript}")
                    
                    elif event_type == 'response.created':
                        self.current_response_id = event.get('response', {}).get('id')
                        self.is_responding = True
                        await self._send_ws_message(browser_ws, json.dumps({
                            'type': 'thinking',
                            'status': 'start'
                        }))
                    
                    elif event_type == 'response.output_item.added':
                        # New output item being created
                        pass
                    
                    elif event_type == 'response.content_part.added':
                        # Content part being added
                        pass
                    
                    elif event_type == 'response.audio_transcript.delta':
                        # Streaming transcript of AI response
                        delta = event.get('delta', '')
                        if delta:
                            await self._send_ws_message(browser_ws, json.dumps({
                                'type': 'response_transcript_delta',
                                'delta': delta
                            }))
                    
                    elif event_type == 'response.audio_transcript.done':
                        # Full transcript of AI response
                        transcript = event.get('transcript', '')
                        if transcript:
                            await self._send_ws_message(browser_ws, json.dumps({
                                'type': 'response_text',
                                'text': transcript
                            }))
                            if config.DEBUG:
                                print(f"💬 AI: {transcript}")
                    
                    elif event_type == 'response.audio.delta':
                        # Audio data from OpenAI
                        audio_base64 = event.get('delta', '')
                        if audio_base64:
                            await self._send_ws_message(browser_ws, json.dumps({
                                'type': 'audio_chunk',
                                'audio': audio_base64
                            }))
                    
                    elif event_type == 'response.audio.done':
                        # Audio complete
                        await self._send_ws_message(browser_ws, json.dumps({
                            'type': 'audio_complete'
                        }))
                    
                    elif event_type == 'response.done':
                        # Response complete
                        self.is_responding = False
                        self.current_response_id = None
                        await self._send_ws_message(browser_ws, json.dumps({
                            'type': 'response_done'
                        }))
                        if config.DEBUG:
                            print("✓ Response complete")
                    
                    elif event_type == 'error':
                        error = event.get('error', {})
                        error_msg = error.get('message', 'Unknown error')
                        
                        # Filter out harmless errors
                        if 'no active response' in error_msg.lower():
                            # This is benign - happens when user speaks but AI wasn't responding
                            if config.DEBUG:
                                print(f"ℹ️ Benign error (ignored): {error_msg}")
                        else:
                            print(f"❌ OpenAI error: {error}")
                            await self._send_ws_message(browser_ws, json.dumps({
                                'type': 'error',
                                'message': error_msg
                            }))
                    
                    elif event_type == 'rate_limits.updated':
                        # Rate limit info
                        pass
                
                except json.JSONDecodeError:
                    print("⚠️ Invalid JSON from OpenAI")
                except Exception as e:
                    print(f"⚠️ Error processing OpenAI event: {e}")
        
        except ConnectionClosed:
            print("⚠️ OpenAI connection closed")
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"❌ OpenAI receive error: {e}")
    
    async def send_greeting(self):
        """Send initial greeting using text-to-speech"""
        if not self.openai_ws:
            return
        
        greeting = "Hello! I'm your STS voice assistant. Just start speaking and I'll respond."
        
        # Create a conversation item with the greeting
        await self.openai_ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [{
                    "type": "input_text",
                    "text": greeting
                }]
            }
        }))
        
        # Request response to speak the greeting
        await self.openai_ws.send(json.dumps({
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"]
            }
        }))
    
    async def send_text_message(self, text: str):
        """Send a text message to OpenAI"""
        if not self.openai_ws:
            return
        
        # Create conversation item
        await self.openai_ws.send(json.dumps({
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": text
                }]
            }
        }))
        
        # Request response
        await self.openai_ws.send(json.dumps({
            "type": "response.create"
        }))
    
    async def save_recording(self, websocket):
        """Save the recorded audio to a WAV file"""
        if websocket not in self.audio_recordings:
            return
        
        audio_chunks = self.audio_recordings[websocket]
        if not audio_chunks:
            del self.audio_recordings[websocket]
            return
        
        try:
            audio_data = b''.join(audio_chunks)
            
            if len(audio_data) == 0:
                del self.audio_recordings[websocket]
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            filepath = self.recordings_dir / filename
            
            with wave.open(str(filepath), 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(config.SAMPLE_RATE)
                wav_file.writeframes(audio_data)
            
            duration = len(audio_data) / (config.SAMPLE_RATE * 2)
            print(f"💾 Recording saved: {filepath} ({duration:.2f}s)")
            
            del self.audio_recordings[websocket]
            
        except Exception as e:
            print(f"⚠️ Error saving recording: {e}")
            if websocket in self.audio_recordings:
                del self.audio_recordings[websocket]
    
    async def cleanup(self):
        """Clean up resources"""
        if config.ENABLE_RECORDINGS:
            for websocket in list(self.audio_recordings.keys()):
                await self.save_recording(websocket)
        
        if self.openai_ws:
            await self.openai_ws.close()


async def serve_static(request):
    """Serve static files"""
    static_dir = Path(__file__).parent / "web_ui"
    
    if request.path == '/' or request.path == '':
        file_path = static_dir / "sts_agent.html"
    else:
        file_path = static_dir / request.path.lstrip('/')
    
    if file_path.exists() and file_path.is_file():
        content_type = 'text/html'
        if file_path.suffix == '.js':
            content_type = 'application/javascript'
        elif file_path.suffix == '.css':
            content_type = 'text/css'
        
        return web.Response(
            body=file_path.read_bytes(),
            content_type=content_type
        )
    
    return web.Response(text="File not found", status=404)


async def websocket_handler(request, agent):
    """Handle WebSocket connections"""
    ws = WebSocketResponse()
    await ws.prepare(request)
    
    # Handle the WebSocket connection (this will run the async for loop)
    await agent.handle_browser_websocket(ws)
    
    return ws


async def init_unified_server(agent):
    """Start unified HTTP and WebSocket server on single port"""
    app = web.Application()
    
    # Static file serving
    app.router.add_get('/{path:.*}', serve_static)
    
    # WebSocket endpoint
    app.router.add_get('/ws', lambda request: websocket_handler(request, agent))
    
    host = config.HOST
    port = config.PORT
    
    print(f"Web interface: http://{host}:{port}")
    print(f"WebSocket server: ws://{host}:{port}/ws")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    await asyncio.Future()


async def main():
    """Main entry point"""
    provider = "Azure OpenAI" if config.USE_AZURE else "OpenAI"
    print("\n" + "=" * 70)
    print(" " * 15 + "STS VOICE AGENT")
    print(" " * 10 + f"(Speech-to-Speech with {provider} Realtime)")
    print("=" * 70)
    print("\n  Direct audio-to-audio processing - no separate STT/TTS")
    print("=" * 70)
    print()
    
    agent = STSVoiceAgent()
    await agent.initialize()
    
    print()
    print("=" * 70)
    print("All systems ready!")
    print("Open http://localhost:8080 in your browser")
    print("=" * 70)
    print()
    
    try:
        await init_unified_server(agent)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

