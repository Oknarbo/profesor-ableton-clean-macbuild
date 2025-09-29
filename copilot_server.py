import json
import os
import requests
import psutil
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

try:
    import socketio  # type: ignore
    import eventlet  # type: ignore
    from groq import Groq  # type: ignore
    import anthropic  # type: ignore
    import openai  # type: ignore
except ImportError as e:
    print(f"Error: Missing required packages - {e}")
    print("Install with: pip install -r requirements.txt")
    exit(1)

# Load environment variables - skip if .env file has issues
try:
    load_dotenv()
except:
    print("Warning: Could not load .env file, using defaults")

class AIProvider:
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gemma3:4b")
        self.ollama_timeout = int(os.getenv("OLLAMA_TIMEOUT", "60"))
        
        # API clients
        self.grok_client = None
        self.groq_client = None
        self.claude_client = None
        self.openai_client = None
        
        # Initialize API clients
        self._init_api_clients()
        
        # Provider priority
        providers_str = os.getenv("AI_PROVIDERS", "groq,ollama,grok,claude,openai")
        self.providers = [p.strip() for p in providers_str.split(",")]
        print(f">> AI Provider priority: {self.providers}")
        
    def _init_api_clients(self):
        """Initialize API clients with keys from environment."""
        # xAI Grok
        xai_key = os.getenv("XAI_API_KEY")
        if xai_key and xai_key != "your_xai_api_key_here":
            try:
                # xAI uses OpenAI-compatible API, so we use openai client
                self.grok_client = openai.OpenAI(
                    api_key=xai_key,
                    base_url="https://api.x.ai/v1"
                )
                print("OK xAI Grok API client initialized")
            except Exception as e:
                print(f"ERROR xAI Grok initialization failed: {e}")
        
        # Groq - GitHub version with placeholder
        # Windows users: If .env doesn't work, replace this line with:
        # groq_key = "your_groq_api_key_here"
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key != "your_groq_api_key_here":
            try:
                self.groq_client = Groq(api_key=groq_key)
                print("OK Groq API client initialized")
            except Exception as e:
                print(f"ERROR Groq initialization failed: {e}")
        
        # Claude (Anthropic)
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        if claude_key and claude_key != "your_anthropic_api_key_here":
            try:
                self.claude_client = anthropic.Anthropic(api_key=claude_key)
                print("OK Claude API client initialized")
            except Exception as e:
                print(f"ERROR Claude initialization failed: {e}")
        
        # OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key and openai_key != "your_openai_api_key_here":
            try:
                self.openai_client = openai.OpenAI(api_key=openai_key)
                print("OK OpenAI API client initialized")
            except Exception as e:
                print(f"ERROR OpenAI initialization failed: {e}")
        
    def ask_ollama(self, question: str) -> Optional[str]:
        """Send question to local Ollama model."""
        try:
            print(f">> Asking Ollama ({self.ollama_model}): {question[:50]}...")
            
            response = requests.post(f"{self.ollama_url}/api/generate", 
                json={
                    "model": self.ollama_model,
                    "prompt": f"As an Ableton Live expert, answer briefly and helpfully: {question}",
                    "stream": False
                }, timeout=self.ollama_timeout)
            
            if response.status_code == 200:
                result = response.json().get("response", "").strip()
                if result:
                    print(f"OK Ollama responded: {result[:50]}...")
                    return result
                else:
                    print("ERROR Ollama returned empty response")
            else:
                print(f"ERROR Ollama HTTP error {response.status_code}: {response.text}")
                
        except requests.exceptions.Timeout:
            print(f"TIMEOUT Ollama timeout after {self.ollama_timeout}s")
        except requests.exceptions.ConnectionError:
            print(">> Ollama connection failed - is 'ollama serve' running?")
        except Exception as e:
            print(f"ERROR Ollama error: {e}")
        return None
    
    def ask_grok(self, question: str) -> Optional[str]:
        """Send question to xAI Grok API."""
        if not self.grok_client:
            print("ERROR Grok client not initialized - check XAI_API_KEY")
            return None
            
        try:
            print(f">> Asking Grok: {question[:50]}...")
            
            response = self.grok_client.chat.completions.create(
                model="grok-4-latest",  # Latest Grok model
                messages=[
                    {"role": "system", "content": "You are Profesor Ableton, a groovy music guru from the comic underground scene! You're an expert Ableton Live producer who talks like a cool, laid-back comic book character. Use phrases like 'Far out!', 'Righteous!', 'That's heavy, man!' and give solid Ableton advice with comic book flair. Keep it helpful but fun!"},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            if result:
                print(f"OK Grok responded: {result[:50]}...")
                return result
            else:
                print("ERROR Grok returned empty response")
                
        except Exception as e:
            print(f"ERROR Grok error: {e}")
        return None
    
    def ask_groq(self, question: str) -> Optional[str]:
        """Send question to Groq API."""
        if not self.groq_client:
            print("ERROR Groq client not initialized - check API key")
            return None
            
        try:
            print(f">> Asking Groq: {question[:50]}...")
            
            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Updated fast Groq model
                messages=[
                    {"role": "system", "content": "You are Profesor Ableton, a groovy music guru from the comic underground scene! You're an expert Ableton Live producer who talks like a cool, laid-back comic book character. Use phrases like 'Far out!', 'Righteous!', 'That's heavy, man!' and give solid Ableton advice with comic book flair. Keep it helpful but fun!"},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            if result:
                print(f"OK Groq responded: {result[:50]}...")
                return result
            else:
                print("ERROR Groq returned empty response")
                
        except Exception as e:
            print(f"ERROR Groq error: {e}")
        return None
    
    def ask_claude(self, question: str) -> Optional[str]:
        """Send question to Claude API."""
        if not self.claude_client:
            print("ERROR Claude client not initialized - check API key")
            return None
            
        try:
            print(f">> Asking Claude: {question[:50]}...")
            
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",  # Fast Claude model
                max_tokens=500,
                system="You are an expert Ableton Live music producer. Answer questions briefly and helpfully.",
                messages=[
                    {"role": "user", "content": question}
                ]
            )
            
            result = response.content[0].text.strip()
            if result:
                print(f"OK Claude responded: {result[:50]}...")
                return result
            else:
                print("ERROR Claude returned empty response")
                
        except Exception as e:
            print(f"ERROR Claude error: {e}")
        return None
    
    def ask_openai(self, question: str) -> Optional[str]:
        """Send question to OpenAI API."""
        if not self.openai_client:
            print("ERROR OpenAI client not initialized - check API key")
            return None
            
        try:
            print(f">> Asking OpenAI: {question[:50]}...")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",  # Affordable OpenAI model
                messages=[
                    {"role": "system", "content": "You are Profesor Ableton, a groovy music guru from the comic underground scene! You're an expert Ableton Live producer who talks like a cool, laid-back comic book character. Use phrases like 'Far out!', 'Righteous!', 'That's heavy, man!' and give solid Ableton advice with comic book flair. Keep it helpful but fun!"},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            result = response.choices[0].message.content.strip()
            if result:
                print(f"OK OpenAI responded: {result[:50]}...")
                return result
            else:
                print("ERROR OpenAI returned empty response")
                
        except Exception as e:
            print(f"ERROR OpenAI error: {e}")
        return None
    
    def get_answer(self, question: str, preferred_model: str = None) -> str:
        """Try to get answer from available providers in priority order."""
        print(f">> Looking for answer to: {question}")
        if preferred_model:
            print(f">> Preferred model: {preferred_model}")
        
        # Use preferred model first if specified
        providers_to_try = []
        if preferred_model and preferred_model in self.providers:
            providers_to_try.append(preferred_model)
            # Add other providers as fallback
            providers_to_try.extend([p for p in self.providers if p != preferred_model])
        else:
            providers_to_try = self.providers
        
        for provider in providers_to_try:
            if provider == "ollama":
                answer = self.ask_ollama(question)
                if answer:
                    return f">> [Ollama] {answer}"
                elif preferred_model == "ollama":
                    return ">> ERROR Ollama not running. Start with 'ollama serve' or switch to Groq (free)"
                    
            elif provider == "grok":
                answer = self.ask_grok(question)
                if answer:
                    return f">> [Grok] {answer}"
                elif preferred_model == "grok":
                    return ">> ERROR xAI Grok requires paid API key. Get credits at https://console.x.ai/ or switch to Groq (free)"
                    
            elif provider == "groq":
                answer = self.ask_groq(question)
                if answer:
                    return f">> [Groq] {answer}"
                    
            elif provider == "claude":
                answer = self.ask_claude(question)
                if answer:
                    return f">> [Claude] {answer}"
                elif preferred_model == "claude":
                    return ">> ERROR Claude requires paid API key. Get one at https://console.anthropic.com/ or switch to Groq (free)"
                    
            elif provider == "openai":
                answer = self.ask_openai(question)
                if answer:
                    return f">> [OpenAI] {answer}"
                elif preferred_model == "openai":
                    return ">> ERROR OpenAI requires paid API key. Get one at https://platform.openai.com/ or switch to Groq (free)"
        
        print("ERROR All AI providers failed")
        
        # Simple fallback responses for common Ableton questions
        question_lower = question.lower()
        if ("arranged view" in question_lower or "arrangement view" in question_lower or 
            "aranged view" in question_lower or ("otvorim" in question_lower and "view" in question_lower) or
            ("otvaram" in question_lower and "view" in question_lower) or "tab key" in question_lower):
            return ">> Arranged View in Ableton Live is the timeline view where you build your full song structure. It shows audio and MIDI clips arranged horizontally across time, allowing you to create intro, verse, chorus, outro sections. Switch between Session View (clip launcher) and Arrangement View using Tab key. Press TAB to switch between views."
        elif "eq" in question_lower and "ableton" in question_lower:
            return ">> EQ (Equalizer) in Ableton Live is used to adjust frequency content of audio. Ableton has EQ Eight (8-band) and EQ Three (3-band). Use it to cut unwanted frequencies, boost desired ones, or create space in your mix. High-pass filters remove low rumble, low-pass filters remove harshness."
        elif "compressor" in question_lower or "compression" in question_lower:
            return ">> Compressor in Ableton reduces dynamic range by lowering loud parts. Key settings: Threshold (when compression starts), Ratio (how much compression), Attack (how fast), Release (how fast it stops). Use for evening out levels, adding punch, or gluing mix elements together."
        elif "session view" in question_lower or ("session" in question_lower and "view" in question_lower):
            return ">> Session View in Ableton Live is the clip launcher view where you can trigger clips in real-time. Each track has clip slots that can contain audio or MIDI clips. Perfect for live performance, jamming, and experimenting with song ideas. Press TAB to switch to Arrangement View."
        elif "reverb" in question_lower:
            return ">> Reverb in Ableton simulates acoustic spaces and adds depth to sounds. Use Reverb device or sends/returns for efficiency. Key parameters: Room Size, Decay Time, Pre-Delay, Dry/Wet. Sends allow multiple tracks to use same reverb, saving CPU and creating cohesive space."
        elif "delay" in question_lower:
            return ">> Delay in Ableton creates echoes and rhythmic effects. Simple Delay for basic echoes, Ping Pong Delay for stereo bouncing, Echo for complex modulated delays. Key settings: Time (sync to tempo), Feedback (number of repeats), Dry/Wet mix."
        elif "midi" in question_lower and ("što" in question_lower or "what" in question_lower):
            return ">> MIDI (Musical Instrument Digital Interface) is a protocol for sending musical information between devices. In Ableton, MIDI clips contain note data, not audio. MIDI notes trigger sounds from instruments. You can edit notes in MIDI Editor, adjust velocity, timing, and duration."
        elif ("ne znam" in question_lower or "početnik" in question_lower or "beginner" in question_lower or 
              ("korak po korak" in question_lower) or ("step by step" in question_lower) or 
              ("kako početi" in question_lower) or ("getting started" in question_lower) or
              ("voditi" in question_lower) or ("guide" in question_lower)):
            return """>> ABLETON LIVE - POČETNI VODIČ:

1. OSNOVNI LAYOUT:
   - Session View (clip launcher) - za jamiranje i eksperimente
   - Arrangement View (timeline) - za stvaranje kompletne pjesme
   - Prebacivanje: TAB tipka

2. PRVI KORACI:
   - Stvori novi Live Set (File > New)
   - Dodaj Audio Track (Ctrl+T)
   - Povuci audio fajl u track ili record mikrofon
   - Play dugme ili Space za reprodukciju

3. OSNOVNI WORKFLOW:
   - Record: R tipka ili Record dugme
   - Play/Stop: Space tipka
   - Tempo: mijenjaj BPM gore lijevo
   - Volume: fader-i desno od track-a

4. SLJEDEĆI KORACI:
   - Dodaj MIDI track za virtuelne instrumente
   - Eksperimentiraj s built-in zvukovima (Drums, Bass, Keys)
   - Koristi Audio Effects (Reverb, Delay, EQ)
   - Snimaj sve u Arrangement View za finalnu pjesmu

SAVJET: Počni s jednostavnim - jedan drum loop, jedna melodija!"""
        elif ("kako napraviti" in question_lower and ("beat" in question_lower or "ritam" in question_lower)):
            return ">> KAKO NAPRAVITI BEAT: 1) Dodaj MIDI track (Ctrl+Shift+T) 2) Povuci Drum Kit iz browser-a 3) Double-click za otvoriti MIDI clip 4) Crtan note-ove: Kick (C1), Snare (D1), Hi-hat (F#1) 5) Koristi kvantizaciju (Ctrl+U) za savršen timing 6) Eksperimentiraj s velocity za dinamiku"
        elif ("kako snimiti" in question_lower or ("record" in question_lower and "audio" in question_lower)):
            return ">> SNIMANJE AUDIO: 1) Dodaj Audio Track (Ctrl+T) 2) Spoji mikrofon/instrument u audio interface 3) Odaberi Input (IO sekcija) 4) Uključi Monitor (Auto/In/Off) 5) Pritisni Record (R) i Play (Space) 6) Snimaj! Savjeti: Postavi levels, koristi click track (metronom)"
        elif ("browser" in question_lower or ("kako naći" in question_lower and "sound" in question_lower)):
            return ">> ABLETON BROWSER: Lijeva strana - sve tvoje zvukove! PLACES (folderi), CATEGORIES (tipovi), PACKS (kolekcije). Povuci-i-stavi iz browsera u track-ove. Pretraži tipkom, koristi Tags za brže pronalaženje. HOT SWAP - zamijeni zvuk bez prekidanja reproduce!"
        else:
            return "ERROR Sorry, all AI providers are currently unavailable. Get a free API key at https://console.groq.com/keys or https://console.x.ai and add it to your .env file."

# Create AI provider and socket.io server
ai = AIProvider()
sio = socketio.Server()
app = socketio.WSGIApp(sio)

@sio.event
def connect(sid, environ):
    print(f">> AI Copilot connected: {sid}")

@sio.event
def disconnect(sid):
    print(f">> AI Copilot disconnected: {sid}")

@sio.event
def command(sid, data):
    """Process AI command and return response."""
    try:
        command = json.loads(data) if isinstance(data, str) else data
        action = command.get("action")
        params = command.get("params", {})
        print(f">> Command received: {action} with params: {params}")

        if action == "ask_ai":
            # Direct question to AI with preferred model
            question = params.get("question", "")
            preferred_model = params.get("preferred_model", None)
            ai_response = ai.get_answer(question, preferred_model)
            response = {"message": ai_response, "type": "ai_answer"}
            
        elif action == "add_track":
            response = {"message": f"Adding audio track: {params.get('name', 'AI Track')}", "explanation": "Audio track is a channel in Ableton for sounds (e.g. drums, vocals)."}
            
        elif action == "explain_midi":
            response = {"message": "MIDI is a language for notes. E.g. number 60 is C4 (middle C on piano).", "explanation": "MIDI sends note and control signals, not sound – like instructions for instruments!"}
            
        elif action == "ableton_help":
            # Contextual help for Ableton
            topic = params.get("topic", "general")
            ai_response = ai.get_answer(f"Explain {topic} in Ableton Live production")
            response = {"message": ai_response, "type": "ableton_help"}
            
        else:
            response = {"message": "Available commands: ask_ai, ableton_help, add_track, explain_midi", "explanation": "Use 'ask_ai' for general questions!"}
        
        sio.emit("response", response, to=sid)
        print(f">> Response sent: {response.get('message', '')[:100]}...")
        return response
    except Exception as e:
        error_response = {"error": str(e)}
        print(f"ERROR Error in command: {e}")
        sio.emit("response", error_response, to=sid)
        return error_response

def find_free_port(start_port=12345):
    """Find a free port starting from start_port."""
    import socket
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    print(" Starting Ableton AI Copilot Server...")
    print(">> Available providers:", ai.providers)
    
    # Memory info
    memory = psutil.virtual_memory()
    print(f">> System memory: {memory.total // (1024**3)}GB total, {memory.available // (1024**3)}GB available")
    
    # Memory save mode check
    if os.getenv("MEMORY_SAVE_MODE") == "true":
        print(">> Memory save mode: Ollama disabled")
    
    # Find free port
    port = find_free_port(12345)
    if port is None:
        print("ERROR: Could not find free port!")
        exit(1)
    
    print(f">> Server running on http://localhost:{port}")
    eventlet.wsgi.server(eventlet.listen(("localhost", port)), app)