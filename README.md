# 🎸 Profesor Ableton - AI Copilot za Ableton Live 🎵

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Groq](https://img.shields.io/badge/AI-Groq%20Free-orange.svg)](https://groq.com)

> *"Far out, dude! Your groovy AI assistant for mastering Ableton Live!"* 🌈

**Profesor Ableton** je pametni AI asistent inspiriran underground comic stripom **Fabulous Furry Freak Brothers**. Pomaže vam učiti Ableton Live s psychedelic stilom i tehnički točnim savjetima!

## ✨ Features

### 🧠 **Multi-AI Provider Support**
- **Groq** (FREE & Fast) - Defaultni, bez ograničenja!
- **xAI Grok** (Paid) - Elon Musk's AI
- **Claude** (Paid) - Anthropic's premium AI  
- **OpenAI** (Paid) - ChatGPT modeli
- **Ollama** (Local) - Offline LLM modeli

### 🎨 **Comic Book Interface**
- **Retro 70s boje** inspirane stripom
- **Comic Sans font** za authentic vibe
- **System tray integration** - uvijek dostupan
- **Model selector** kao u Cursoru
- **Keyboard shortcuts** (Ctrl+H/S, Escape)

### 🎵 **Ableton Live Expertise**
- **Beginner tutorials** korak po korak
- **Advanced produkcija** - mixing, mastering, synthesis
- **MIDI & Audio** objašnjenja
- **Plugin usage** - EQ, compressor, reverb, delay
- **Workflow tips** - Session vs Arrangement View

### 💬 **Groovy Personality**
- **Comic book fraze**: "Far out!", "Righteous!", "That's heavy, man!"
- **Laid-back savjeti** s tehnički točnim informacijama
- **Underground strip osjećaj** iz 70-ih

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+**
- **Internet connection** (za AI APIs)

### 1. Installation
```bash
git clone https://github.com/your-username/profesor-ableton.git
cd profesor-ableton
pip install -r requirements.txt
```

### 2. Get FREE Groq API Key
1. Idite na [console.groq.com](https://console.groq.com/keys)
2. Registrirajte se (besplatno!)
3. Generirajte API ključ
4. Kopirajte ključ

### 3. Configuration

**Option A: .env file (Linux/Mac)**
```bash
# Copy template
cp env_example.txt .env

# Edit .env and add your key
GROQ_API_KEY=your_actual_groq_key_here
```

**Option B: Code modification (Windows - if .env doesn't work)**
If you get encoding errors with .env files on Windows:

1. Open `copilot_server.py` 
2. Find line ~63: `groq_key = os.getenv("GROQ_API_KEY")`
3. Replace with: `groq_key = "your_actual_groq_key_here"`

**Why hardcode?** Windows sometimes has .env encoding issues. Direct hardcoding works 100%.

# Optional: Other providers (paid)
# XAI_API_KEY=your_xai_key_here
# ANTHROPIC_API_KEY=your_claude_key_here  
# OPENAI_API_KEY=your_openai_key_here
```

### 4. Launch
```bash
# Option 1: Separate terminals
python copilot_server.py    # Terminal 1
python gui_copilot.py       # Terminal 2

# Option 2: Batch script (Windows)
start_copilot.bat

# Option 3: Python launcher
python launch_copilot.py
```

## 🎯 Usage Examples

### Basic Questions
```
🔵 You: što je arranged view?
🤖 Profesor: Far out! Arranged View is like your timeline canvas, man! 
   That's where you build your full song structure - intro, verse, 
   chorus, outro. Press TAB to switch between Session and Arrangement 
   views. Righteous for creating complete tracks!
```

### Advanced Production
```
🔵 You: kako napraviti sidechain compression?
🤖 Profesor: Heavy question, dude! Sidechain is when one sound 
   "ducks" another - that pumping effect in house music! 
   Route your kick to Compressor's sidechain input, adjust 
   threshold & ratio. Total groove maker!
```

### Model Selection
- **Dropdown selector** kao u Cursoru
- **Instant switching** između AI modela
- **Error handling** za neplaćene API-jeve
- **Model indicators** u odgovorima: `[Groq]`, `[Claude]`, etc.

## 🛠️ Advanced Setup

### Additional AI Providers

#### xAI Grok (Paid)
```bash
# Get API key from https://console.x.ai/
XAI_API_KEY=xai-your_key_here
AI_PROVIDERS=groq,grok
```

#### Claude (Paid)
```bash  
# Get API key from https://console.anthropic.com/
ANTHROPIC_API_KEY=sk-ant-your_key_here
AI_PROVIDERS=groq,claude
```

#### OpenAI (Paid)
```bash
# Get API key from https://platform.openai.com/
OPENAI_API_KEY=sk-your_key_here
AI_PROVIDERS=groq,openai
```

#### Ollama (Local/Free)
```bash
# Install Ollama: https://ollama.ai/
ollama serve
ollama pull llama3.1:8b

# In .env:
AI_PROVIDERS=groq,ollama
OLLAMA_MODEL=llama3.1:8b
```

### Memory Optimization
```bash
# Disable Ollama to save RAM
python disable_ollama.py

# Re-enable later
python enable_ollama.py
```

## 📁 Project Structure
```
profesor-ableton/
├── copilot_server.py      # Main AI server
├── gui_copilot.py         # Groovy GUI interface  
├── requirements.txt       # Python dependencies
├── .env.example          # Configuration template
├── README.md             # This file
├── LICENSE               # MIT License
├── start_copilot.bat     # Windows launcher
├── launch_copilot.py     # Cross-platform launcher
├── disable_ollama.py     # Memory optimization
├── enable_ollama.py      # Re-enable Ollama
└── midi_test.py          # MIDI example
```

## 🤝 Contributing

Profesor Ableton je open source! Contributions su welcome:

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b groovy-feature`)
3. **Commit** changes (`git commit -am 'Add some groovy feature'`)
4. **Push** to branch (`git push origin groovy-feature`)
5. **Create** Pull Request

### Development Ideas
- 🎹 **Max for Live integration** - direktno u Ableton interface
- 🎵 **MIDI generation** - AI stvara MIDI patterns
- 🎧 **Audio analysis** - AI analizira vaše pjesme
- 🌍 **More languages** - lokalizacija
- 🎨 **Custom themes** - više comic book stilova

## 🐛 Troubleshooting

### Common Issues

#### "Can't connect to server"
```bash
# Check if server is running
netstat -ano | findstr :12345

# Kill existing process
taskkill /PID <process_id> /F

# Restart server
python copilot_server.py
```

#### "All AI providers unavailable"
- Provjerite internetsku vezu
- Potvrdite GROQ_API_KEY u `.env`
- Testirajte API ključ na [console.groq.com](https://console.groq.com)

#### UnicodeEncodeError (Windows)
- Fixed! Emoji su zamijenjeni text indikatorima
- Windows terminal fully supported

#### GUI Window Disappears
- System tray integration dodana
- Koristite Ctrl+H/S za show/hide
- Kliknite tray ikonu

## 📊 Performance

### Speed Comparison
- **Groq**: ⚡ 1-2s (FREE!)
- **Claude**: 🐌 3-5s (Paid)
- **OpenAI**: 🐌 2-4s (Paid)  
- **Ollama**: 🐢 5-15s (Local)

### Resource Usage
- **RAM**: ~50MB (bez Ollama), ~2GB (s Ollama)
- **CPU**: Minimal podczas idle
- **Network**: Samo za AI requests

## 🎵 Philosophy

> *"Music is the universal language, and technology should enhance creativity, not complicate it. Profesor Ableton bridges the gap between human creativity and AI assistance with a groovy, approachable personality that makes learning fun!"*

Inspired by the counterculture spirit of **Fabulous Furry Freak Brothers**, Profesor Ableton kombinira:
- 🎪 **Fun & Playful** interface
- 🧠 **Serious Technical** knowledge  
- 🌈 **Creative Freedom** u učenju
- 🎵 **Music Production** expertise

## 📄 License

MIT License - feel free to fork, modify, and share the groovy vibes!

## 🙏 Acknowledgments

- **Gilbert Shelton** za Fabulous Furry Freak Brothers inspiraciju
- **Groq** za amazing free AI API
- **Ableton** za najbolji DAW ever
- **Python community** za fantastic libraries
- **Open source** movement za making this possible

---

**🎸 Keep it groovy, keep it creative! 🎵**

*Made with ❤️ and lots of ☕ by music lovers for music lovers*