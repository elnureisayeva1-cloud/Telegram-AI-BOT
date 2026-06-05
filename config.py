"""
╔══════════════════════════════════════════════════════════════════╗
║              ☀️  SUN AI BOT — CONFIGURATION                      ║
╠══════════════════════════════════════════════════════════════════╣
║  ⚠️  ADD YOUR TOKENS BELOW BEFORE RUNNING THE BOT!               ║
║  At least TELEGRAM_TOKEN + one AI provider key is required.      ║
╚══════════════════════════════════════════════════════════════════╝

HOW TO GET YOUR TOKENS:
────────────────────────────────────────────────────────────────────

1. TELEGRAM_TOKEN (REQUIRED)
   • Open Telegram → search @BotFather → send /newbot
   • Copy the token (e.g. 123456789:ABCdef...)

2. AI PROVIDER KEYS — add as many as you want (at least one required)

   🔵 ANTHROPIC (Claude)
   • https://console.anthropic.com/ → API Keys → Create Key
   • Looks like: sk-ant-...

   🟢 OPENAI (ChatGPT / GPT-4)
   • https://platform.openai.com/api-keys → Create new secret key
   • Looks like: sk-...

   🟡 GOOGLE (Gemini)
   • https://aistudio.google.com/app/apikey → Create API Key
   • Looks like: AIza...

   🔴 XAI (Grok)
   • https://console.x.ai/ → API Keys → Create Key
   • Looks like: xai-...

3. STABILITY_API_KEY (OPTIONAL — for HD image generation)
   • https://platform.stability.ai/ → API Keys
   • If not set, free fallback (pollinations.ai) is used

────────────────────────────────────────────────────────────────────
"""

# ═══════════════════════════════════════════════════
#   EDIT BELOW THIS LINE — ADD YOUR TOKENS
# ═══════════════════════════════════════════════════

# 🔴 REQUIRED
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# ── AI PROVIDER KEYS (add whichever you have) ──────
# Providers with a valid key will appear as options in the bot.
# Leave unused ones as-is — they'll simply be hidden from users.

ANTHROPIC_API_KEY  = "YOUR_ANTHROPIC_API_KEY_HERE"   # Claude (claude-opus-4-5)
OPENAI_API_KEY     = "YOUR_OPENAI_API_KEY_HERE"       # ChatGPT (gpt-4o)
GOOGLE_API_KEY     = "YOUR_GOOGLE_GEMINI_API_KEY_HERE" # Gemini (gemini-1.5-pro)
XAI_API_KEY        = "YOUR_XAI_GROK_API_KEY_HERE"    # Grok (grok-3)

# ── IMAGE GENERATION (optional) ────────────────────
STABILITY_API_KEY  = "YOUR_STABILITY_API_KEY_HERE"

# 🟠 OPTIONAL — Ücretsiz, FLUX / SD modelleri için
# https://huggingface.co/settings/tokens → New token (read)
HUGGINGFACE_API_KEY = "YOUR_HUGGINGFACE_API_KEY_HERE"

# ═══════════════════════════════════════════════════
#   BOT SETTINGS
# ═══════════════════════════════════════════════════

BOT_CONFIG = {
    "version": "2.0.0",
    "created": "2025",
    "name": "Sun AI",
    "max_history": 20,
    "max_tokens": 2048,
    "image_width": 1024,
    "image_height": 1024,
    # Default provider shown to new users (must be one of the keys below)
    # Options: "anthropic", "openai", "google", "xai"
    "default_provider": "anthropic",
}

# ═══════════════════════════════════════════════════
#   PROXY SETTINGS
#   If Telegram is blocked in your country/network,
#   set PROXY_URL to route traffic through a proxy.
# ═══════════════════════════════════════════════════
#
#  Examples:
#    SOCKS5 proxy:  "socks5://user:pass@host:port"
#    HTTP proxy:    "http://user:pass@host:port"
#    No proxy:       None
#
PROXY_URL = None   # e.g. "socks5://127.0.0.1:1080"

# Connection timeout in seconds (increase if on slow network)
CONNECT_TIMEOUT = 30
READ_TIMEOUT    = 30
WRITE_TIMEOUT   = 30
POOL_TIMEOUT    = 30

# ── Provider display info (do not edit) ────────────
PROVIDERS = {
    "anthropic": {
        "name": "Claude (Anthropic)",
        "emoji": "🔵",
        "model": "claude-opus-4-5",
        "key_var": ANTHROPIC_API_KEY,
        "placeholder": "YOUR_ANTHROPIC_API_KEY_HERE",
        "url": "https://console.anthropic.com/",
    },
    "openai": {
        "name": "ChatGPT (OpenAI)",
        "emoji": "🟢",
        "model": "gpt-4o",
        "key_var": OPENAI_API_KEY,
        "placeholder": "YOUR_OPENAI_API_KEY_HERE",
        "url": "https://platform.openai.com/api-keys",
    },
    "google": {
        "name": "Gemini (Google)",
        "emoji": "🟡",
        "model": "gemini-1.5-pro",
        "key_var": GOOGLE_API_KEY,
        "placeholder": "YOUR_GOOGLE_GEMINI_API_KEY_HERE",
        "url": "https://aistudio.google.com/app/apikey",
    },
    "xai": {
        "name": "Grok (xAI)",
        "emoji": "🔴",
        "model": "grok-3",
        "key_var": XAI_API_KEY,
        "placeholder": "YOUR_XAI_GROK_API_KEY_HERE",
        "url": "https://console.x.ai/",
    },
}

def get_active_providers() -> dict:
    """Returns only providers that have a real API key configured."""
    return {
        pid: info for pid, info in PROVIDERS.items()
        if info["key_var"] and info["key_var"] != info["placeholder"]
    }
