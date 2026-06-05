# ☀️ Sun AI — Telegram Bot

A powerful, multilingual AI assistant for Telegram supporting **Claude · ChatGPT · Gemini · Grok** — use any or all at once!

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue?style=flat-square&logo=telegram)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **Multi-Model AI** | Claude, ChatGPT, Gemini, Grok — switch anytime with `/ai` |
| 💬 **AI Chat** | Intelligent conversation with memory |
| 🌐 **All Languages** | Auto-detects and replies in any world language |
| 🎨 **Image Generation** | Create AI images from text prompts |
| 🖼️ **6 Art Styles** | Photorealistic, Digital Art, Oil Painting, Sketch, Anime, Fantasy |
| 💾 **Memory** | Per-user conversation history |
| 💻 **Code Generator** | Generate code in any language |
| 📄 **Summarizer & Translator** | Built-in tools |

---

## 🚀 Quick Start

```bash
git clone https://github.com/elnureisayeva1-cloud/Telegram-AI-BOT.git
cd sun-ai-bot
pip install -r requirements.txt
```

Open **`config.py`** and add your tokens:

```python
TELEGRAM_TOKEN    = "YOUR_TELEGRAM_BOT_TOKEN_HERE"   # Required

ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY_HERE"    # Claude
OPENAI_API_KEY    = "YOUR_OPENAI_API_KEY_HERE"        # ChatGPT
GOOGLE_API_KEY    = "YOUR_GOOGLE_GEMINI_API_KEY_HERE" # Gemini
XAI_API_KEY       = "YOUR_XAI_GROK_API_KEY_HERE"     # Grok
```

> You only need **at least one** AI provider key. Add as many as you want — only configured ones appear in the bot.

```bash
python bot.py
```

---

## 🔑 Getting API Keys

| Provider | Where to get it |
|---|---|
| 🔵 **Anthropic (Claude)** | [console.anthropic.com](https://console.anthropic.com/) |
| 🟢 **OpenAI (ChatGPT)** | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| 🟡 **Google (Gemini)** | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |
| 🔴 **xAI (Grok)** | [console.x.ai](https://console.x.ai/) |
| 📸 **Stability AI** *(optional)* | [platform.stability.ai](https://platform.stability.ai/) |
| 🤖 **Telegram Token** | [@BotFather](https://t.me/BotFather) → `/newbot` |

---

## 📱 Commands

| Command | Description |
|---|---|
| `/start` | Welcome screen |
| `/ai` | Switch between AI models |
| `/draw <prompt>` | Generate an image |
| `/style` | Choose image art style |
| `/translate <text>` | Translate to English |
| `/summarize <text>` | Summarize text |
| `/code <task>` | Generate code |
| `/clear` | Clear conversation history |
| `/help` | All commands |

---

## 📁 Structure

```
sun-ai-bot/
├── bot.py           # Main bot
├── config.py        # ← Edit this with your tokens
├── requirements.txt
└── README.md
```

---

## ⚠️ Notes

- Add `config.py` to `.gitignore` before pushing to GitHub to keep your keys safe.
- At startup, the bot checks which keys are configured and only shows those providers.
- Switching AI model clears conversation history automatically.

---

MIT License · Built with ❤️ using [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
