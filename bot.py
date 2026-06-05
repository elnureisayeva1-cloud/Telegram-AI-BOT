"""
╔══════════════════════════════════════════════════════╗
║              ☀️  SUN AI - Telegram Bot               ║
║   Multi-Provider AI: Claude · ChatGPT · Gemini · Grok║
╚══════════════════════════════════════════════════════╝
"""

import sys
import logging
import asyncio
import base64
from typing import Optional

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from telegram.constants import ParseMode, ChatAction
from telegram.request import HTTPXRequest
import httpx

from config import (
    TELEGRAM_TOKEN, BOT_CONFIG, PROVIDERS,
    ANTHROPIC_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY, XAI_API_KEY,
    STABILITY_API_KEY, HUGGINGFACE_API_KEY, get_active_providers,
    PROXY_URL, CONNECT_TIMEOUT, READ_TIMEOUT, WRITE_TIMEOUT, POOL_TIMEOUT,
)

# ─── Token Check ─────────────────────────────────────────────────────────────
def check_tokens():
    errors = []

    if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        errors.append(("TELEGRAM_TOKEN", "Get from @BotFather on Telegram → /newbot"))

    active = get_active_providers()
    if not active:
        errors.append((
            "AI PROVIDER KEY",
            "Add at least ONE of: ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY / XAI_API_KEY\n"
            "     in config.py"
        ))

    if errors:
        print("\n" + "═" * 64)
        print("  ☀️  SUN AI BOT — TOKEN CONFIGURATION REQUIRED")
        print("═" * 64)
        print("\n  ❌  The bot cannot start — missing required tokens:\n")
        for name, hint in errors:
            print(f"  📌  {name}")
            print(f"      → {hint}\n")
        print("  Open  config.py  and fill in your tokens, then re-run.")
        print("═" * 64 + "\n")
        sys.exit(1)

    print("\n" + "═" * 64)
    print("  ☀️  SUN AI BOT — Active AI Providers:")
    for pid, info in active.items():
        print(f"  {info['emoji']}  {info['name']}  ({info['model']})")
    print("═" * 64 + "\n")

check_tokens()

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("SunAI")

# ─── Lazy-load provider SDKs ──────────────────────────────────────────────────
active_providers = get_active_providers()

_anthropic_client = None
_openai_client    = None
_google_client    = None

if "anthropic" in active_providers:
    import anthropic as _anthropic_sdk
    _anthropic_client = _anthropic_sdk.Anthropic(api_key=ANTHROPIC_API_KEY)

if "openai" in active_providers:
    from openai import AsyncOpenAI
    _openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

if "google" in active_providers:
    import google.generativeai as genai
    genai.configure(api_key=GOOGLE_API_KEY)
    _google_client = genai.GenerativeModel("gemini-1.5-pro")

# xAI Grok uses OpenAI-compatible API — no extra SDK needed

# ─── Session Store ────────────────────────────────────────────────────────────
user_sessions: dict[int, dict] = {}

def get_session(user_id: int) -> dict:
    if user_id not in user_sessions:
        # Default to first available provider
        default = BOT_CONFIG.get("default_provider", "anthropic")
        if default not in active_providers:
            default = next(iter(active_providers))
        user_sessions[user_id] = {
            "history": [],
            "provider": default,
            "mode": "chat",
            "image_style": "photorealistic",
        }
    return user_sessions[user_id]

# ─── System Prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are Sun AI — a warm, intelligent, and creative AI assistant inside Telegram.
- Always respond in the SAME language the user writes in. Auto-detect every message.
- Be concise yet thorough. Use Telegram markdown where helpful.
- Help with anything: questions, coding, writing, math, translation, analysis, creativity.
- If asked who you are: you are Sun AI, a powerful multi-model AI assistant.
"""

# ─── AI Call ──────────────────────────────────────────────────────────────────
async def ask_ai(user_id: int, message: str) -> str:
    session = get_session(user_id)
    provider = session["provider"]
    session["history"].append({"role": "user", "content": message})
    history = session["history"][-BOT_CONFIG["max_history"]:]

    try:
        reply = ""

        # ── Claude (Anthropic) ────────────────────────────────────────────────
        if provider == "anthropic":
            resp = _anthropic_client.messages.create(
                model=PROVIDERS["anthropic"]["model"],
                max_tokens=BOT_CONFIG["max_tokens"],
                system=SYSTEM_PROMPT,
                messages=history,
            )
            reply = resp.content[0].text

        # ── ChatGPT (OpenAI) ──────────────────────────────────────────────────
        elif provider == "openai":
            msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history
            resp = await _openai_client.chat.completions.create(
                model=PROVIDERS["openai"]["model"],
                max_tokens=BOT_CONFIG["max_tokens"],
                messages=msgs,
            )
            reply = resp.choices[0].message.content

        # ── Gemini (Google) ───────────────────────────────────────────────────
        elif provider == "google":
            # Build history in Gemini format
            gemini_history = []
            for msg in history[:-1]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [msg["content"]]})
            chat = _google_client.start_chat(history=gemini_history)
            resp = chat.send_message(SYSTEM_PROMPT + "\n\n" + message if not gemini_history else message)
            reply = resp.text

        # ── Grok (xAI) ────────────────────────────────────────────────────────
        elif provider == "xai":
            msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + history
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": PROVIDERS["xai"]["model"],
                        "messages": msgs,
                        "max_tokens": BOT_CONFIG["max_tokens"],
                    },
                )
                r.raise_for_status()
                reply = r.json()["choices"][0]["message"]["content"]

        session["history"].append({"role": "assistant", "content": reply})
        return reply

    except Exception as e:
        logger.error(f"AI error [{provider}]: {e}")
        return f"⚠️ Error from {PROVIDERS[provider]['name']}: {str(e)[:200]}\n\nTry switching provider with /ai"

# ─── Image Generation ─────────────────────────────────────────────────────────
async def generate_image(prompt: str, style: str = "photorealistic") -> Optional[bytes]:
    style_prompts = {
        "photorealistic": "photorealistic, highly detailed, 8k, professional photography, sharp focus",
        "digital_art":    "digital art, vibrant colors, concept art, artstation, deviantart",
        "oil_painting":   "oil painting, classical art style, textured brushstrokes, museum quality",
        "sketch":         "pencil sketch, hand-drawn, detailed line art, black and white ink",
        "anime":          "anime style, manga art, studio ghibli, beautiful, colorful, detailed",
        "fantasy":        "fantasy art, magical, ethereal, epic, dramatic lighting, mystical",
    }
    enhanced = f"{prompt}, {style_prompts.get(style, '')}"
    negative = "blurry, bad quality, ugly, distorted, watermark, text, nsfw"

    # ── 1. Stability AI (ücretli, en iyi kalite) ──────────────────────────────
    if STABILITY_API_KEY and STABILITY_API_KEY != "YOUR_STABILITY_API_KEY_HERE":
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                r = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={"Authorization": f"Bearer {STABILITY_API_KEY}", "Accept": "application/json"},
                    json={
                        "text_prompts": [
                            {"text": enhanced, "weight": 1.0},
                            {"text": negative, "weight": -1.0},
                        ],
                        "cfg_scale": 7, "width": 1024, "height": 1024, "steps": 30, "samples": 1,
                    },
                )
                if r.status_code == 200:
                    logger.info("Image: Stability AI ✅")
                    return base64.b64decode(r.json()["artifacts"][0]["base64"])
        except Exception as e:
            logger.error(f"Stability AI: {e}")

    # ── 2. Hugging Face — FLUX.1-schnell (ücretsiz, yüksek kalite) ────────────
    if HUGGINGFACE_API_KEY and HUGGINGFACE_API_KEY != "YOUR_HUGGINGFACE_API_KEY_HERE":
        for hf_model in [
            "black-forest-labs/FLUX.1-schnell",
            "stabilityai/stable-diffusion-3-medium-diffusers",
            "runwayml/stable-diffusion-v1-5",
        ]:
            try:
                async with httpx.AsyncClient(timeout=120) as client:
                    r = await client.post(
                        f"https://api-inference.huggingface.co/models/{hf_model}",
                        headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                        json={"inputs": enhanced, "parameters": {"negative_prompt": negative}},
                    )
                    if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                        logger.info(f"Image: HuggingFace {hf_model} ✅")
                        return r.content
                    elif r.status_code == 503:
                        logger.info(f"HF model {hf_model} loading, trying next...")
                        continue
            except Exception as e:
                logger.error(f"HuggingFace {hf_model}: {e}")

    # ── 3. Stable Horde (tamamen ücretsiz, topluluk GPU'ları) ─────────────────
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                "https://stablehorde.net/api/v2/generate/async",
                headers={"apikey": "0000000000", "Content-Type": "application/json"},
                json={
                    "prompt": enhanced + " ### " + negative,
                    "params": {
                        "width": 512, "height": 512,
                        "steps": 25, "n": 1,
                        "sampler_name": "k_euler_a",
                        "cfg_scale": 7.5,
                    },
                    "nsfw": False,
                    "censor_nsfw": True,
                    "models": ["SDXL 1.0", "stable_diffusion"],
                },
            )
            if r.status_code == 202:
                job_id = r.json().get("id")
                logger.info(f"Horde job submitted: {job_id}")
                for attempt in range(20):
                    await asyncio.sleep(6)
                    check = await client.get(
                        f"https://stablehorde.net/api/v2/generate/check/{job_id}",
                        headers={"apikey": "0000000000"},
                    )
                    data = check.json()
                    logger.info(f"Horde: done={data.get('done')}, queue={data.get('queue_position')}")
                    if data.get("done"):
                        status = await client.get(
                            f"https://stablehorde.net/api/v2/generate/status/{job_id}",
                            headers={"apikey": "0000000000"},
                        )
                        generations = status.json().get("generations", [])
                        if generations:
                            img_data = generations[0].get("img", "")
                            if img_data.startswith("http"):
                                img_r = await client.get(img_data)
                                if img_r.status_code == 200:
                                    logger.info("Image: Stable Horde ✅")
                                    return img_r.content
                            elif img_data:
                                logger.info("Image: Stable Horde (b64) ✅")
                                return base64.b64decode(img_data)
                        break
    except Exception as e:
        logger.error(f"Stable Horde: {e}")

    # ── 4. Dezgo (ücretsiz REST API, kayıt gerekmez) ──────────────────────────
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            r = await client.post(
                "https://api.dezgo.com/text2image",
                headers={"X-Dezgo-Key": "DEZGO_FREE"},
                data={
                    "prompt": enhanced[:500],
                    "negative_prompt": negative,
                    "guidance": 7.5,
                    "steps": 25,
                    "width": 512,
                    "height": 512,
                    "format": "png",
                },
            )
            if r.status_code == 200 and len(r.content) > 5000:
                logger.info("Image: Dezgo ✅")
                return r.content
    except Exception as e:
        logger.error(f"Dezgo: {e}")

    logger.error("Image: all providers failed ❌")
    return None

# ─── Keyboards ────────────────────────────────────────────────────────────────
def kb_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Switch AI Model", callback_data="menu_ai"),
         InlineKeyboardButton("🎨 Draw Image",      callback_data="mode_image")],
        [InlineKeyboardButton("🖼️ Image Style",     callback_data="menu_style"),
         InlineKeyboardButton("🗑️ Clear History",   callback_data="clear_history")],
        [InlineKeyboardButton("ℹ️ About",            callback_data="about")],
    ])

def kb_ai_providers(current: str) -> InlineKeyboardMarkup:
    buttons = []
    for pid, info in active_providers.items():
        check = " ✅" if pid == current else ""
        buttons.append([InlineKeyboardButton(f"{info['emoji']} {info['name']}{check}", callback_data=f"ai_{pid}")])
    buttons.append([InlineKeyboardButton("◀️ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)

def kb_style(current: str) -> InlineKeyboardMarkup:
    styles = [
        ("📸 Photorealistic", "photorealistic"),
        ("🎨 Digital Art",    "digital_art"),
        ("🖼️ Oil Painting",  "oil_painting"),
        ("✏️ Sketch",        "sketch"),
        ("🌸 Anime",         "anime"),
        ("🔮 Fantasy",       "fantasy"),
    ]
    buttons = []
    for label, sid in styles:
        check = " ✅" if sid == current else ""
        buttons.append([InlineKeyboardButton(f"{label}{check}", callback_data=f"style_{sid}")])
    buttons.append([InlineKeyboardButton("◀️ Back", callback_data="menu_back")])
    return InlineKeyboardMarkup(buttons)

# ─── Commands ─────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    session = get_session(user.id)
    pinfo = active_providers.get(session["provider"], {})
    provider_line = f"{pinfo.get('emoji','🤖')} Currently using: *{pinfo.get('name','Unknown')}*"

    text = (
        f"☀️ *Welcome to Sun AI, {user.first_name}!*\n\n"
        "Your intelligent AI companion — powered by the world's best models.\n\n"
        "💬 *Chat* — Ask anything in any language\n"
        "🎨 *Draw* — `/draw sunset over Istanbul`\n"
        "✍️ *Write* — Essays, poems, stories, code\n"
        "🌍 *Translate* — `/translate your text`\n"
        "📄 *Summarize* — `/summarize long text`\n"
        "💻 *Code* — `/code what to build`\n\n"
        f"{provider_line}\n\n"
        "Use /ai to switch AI models anytime!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb_main())

async def cmd_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    text = "🤖 *Choose your AI model:*\n\nAll models support every language and have conversation memory."
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=kb_ai_providers(session["provider"]))

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    providers_list = "\n".join(
        f"  {info['emoji']} {info['name']} — `{info['model']}`"
        for info in active_providers.values()
    )
    text = (
        "☀️ *Sun AI — Commands*\n\n"
        "💬 *Chat*\n"
        "`/start` — Welcome\n`/help` — This menu\n`/clear` — Clear history\n`/ai` — Switch AI model\n\n"
        "🎨 *Images*\n"
        "`/draw <prompt>` — Generate image\n`/style` — Art style\n\n"
        "🛠️ *Tools*\n"
        "`/translate <text>` — Translate\n`/summarize <text>` — Summarize\n`/code <task>` — Generate code\n\n"
        f"🤖 *Active AI Models:*\n{providers_list}\n\n"
        "🌐 All world languages supported!"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def cmd_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_session(update.effective_user.id)["history"] = []
    await update.message.reply_text("🗑️ History cleared! Fresh start ✨")

async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    providers_text = " · ".join(f"{i['emoji']} {i['name']}" for i in active_providers.values())
    text = (
        "☀️ *Sun AI*\n\n"
        f"*Active models:* {providers_text}\n\n"
        "🌐 All world languages\n"
        "🎨 6 image art styles\n"
        "💾 Per-user conversation memory\n"
        "🔄 Switch AI models anytime\n"
        "⚡ Fast & reliable\n\n"
        f"*Version:* {BOT_CONFIG['version']} · Open source on GitHub"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def cmd_draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("🎨 Usage: `/draw a cat riding a dragon`", parse_mode=ParseMode.MARKDOWN)
        return
    session = get_session(update.effective_user.id)
    style = session.get("image_style", "photorealistic")
    msg = await update.message.reply_text(f"🎨 Generating...\n_{prompt}_", parse_mode=ParseMode.MARKDOWN)
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_PHOTO)
    img = await generate_image(prompt, style)
    if img:
        await msg.delete()
        await update.message.reply_photo(img, caption=f"☀️ *Sun AI*\n_{prompt}_ · _{style}_", parse_mode=ParseMode.MARKDOWN)
    else:
        await msg.edit_text("❌ Could not generate image. Try a different prompt.")

async def cmd_translate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: `/translate <text>`", parse_mode=ParseMode.MARKDOWN); return
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    result = await ask_ai(update.effective_user.id, f"Translate to English (return translation only):\n{text}")
    await update.message.reply_text(f"🌐 *Translation:*\n{result}", parse_mode=ParseMode.MARKDOWN)

async def cmd_summarize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Usage: `/summarize <text>`", parse_mode=ParseMode.MARKDOWN); return
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    result = await ask_ai(update.effective_user.id, f"Summarize concisely:\n{text}")
    await update.message.reply_text(f"📄 *Summary:*\n{result}", parse_mode=ParseMode.MARKDOWN)

async def cmd_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = " ".join(context.args)
    if not task:
        await update.message.reply_text("Usage: `/code <what to build>`", parse_mode=ParseMode.MARKDOWN); return
    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    result = await ask_ai(update.effective_user.id, f"Write clean, commented code for: {task}")
    await update.message.reply_text(result, parse_mode=ParseMode.MARKDOWN)

async def cmd_style(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = get_session(update.effective_user.id)
    await update.message.reply_text("🎨 *Choose image style:*", parse_mode=ParseMode.MARKDOWN,
                                     reply_markup=kb_style(session.get("image_style", "photorealistic")))

# ─── Message Handler ──────────────────────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user_id = update.effective_user.id
    session = get_session(user_id)
    text = update.message.text.strip()

    if session.get("mode") == "image":
        await context.bot.send_chat_action(update.effective_chat.id, ChatAction.UPLOAD_PHOTO)
        msg = await update.message.reply_text(f"🎨 Drawing: _{text}_...", parse_mode=ParseMode.MARKDOWN)
        img = await generate_image(text, session.get("image_style", "photorealistic"))
        if img:
            await msg.delete()
            await update.message.reply_photo(img, caption=f"☀️ _{text}_", parse_mode=ParseMode.MARKDOWN)
        else:
            await msg.edit_text("❌ Couldn't generate image. Try another description.")
        return

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
    reply = await ask_ai(user_id, text)
    chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
    for chunk in chunks:
        try:
            await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await update.message.reply_text(chunk)

# ─── Callback Handler ─────────────────────────────────────────────────────────
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    user_id = update.effective_user.id
    session = get_session(user_id)

    if data.startswith("ai_"):
        pid = data[3:]
        if pid in active_providers:
            session["provider"] = pid
            session["history"] = []
            info = active_providers[pid]
            await q.edit_message_text(
                f"{info['emoji']} *Switched to {info['name']}!*\n"
                f"Model: `{info['model']}`\n\n"
                "Conversation history cleared. Say hello! 👋",
                parse_mode=ParseMode.MARKDOWN,
            )

    elif data == "menu_ai":
        await q.edit_message_text("🤖 *Choose your AI model:*",
                                   parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=kb_ai_providers(session["provider"]))

    elif data == "mode_image":
        session["mode"] = "image"
        await q.edit_message_text("🎨 *Image mode!* Describe anything and I'll draw it.\nUse /style to pick art style.", parse_mode=ParseMode.MARKDOWN)

    elif data == "menu_style":
        await q.edit_message_text("🎨 *Choose art style:*", parse_mode=ParseMode.MARKDOWN,
                                   reply_markup=kb_style(session.get("image_style", "photorealistic")))

    elif data.startswith("style_"):
        sid = data[6:]
        session["image_style"] = sid
        session["mode"] = "chat"
        await q.edit_message_text(f"✅ Style set to *{sid.replace('_', ' ').title()}*!\nUse `/draw <prompt>` to generate.", parse_mode=ParseMode.MARKDOWN)

    elif data == "clear_history":
        session["history"] = []
        await q.edit_message_text("🗑️ *History cleared!* Fresh start ✨", parse_mode=ParseMode.MARKDOWN)

    elif data == "about":
        providers_text = "\n".join(f"  {i['emoji']} {i['name']} — {i['model']}" for i in active_providers.values())
        await q.edit_message_text(
            f"☀️ *Sun AI v{BOT_CONFIG['version']}*\n\n*Active models:*\n{providers_text}\n\n"
            "🌐 All world languages · 🎨 6 image styles · 💾 Memory per user",
            parse_mode=ParseMode.MARKDOWN,
        )

    elif data == "menu_back":
        pinfo = active_providers.get(session["provider"], {})
        await q.edit_message_text(
            f"☀️ *Sun AI* — {pinfo.get('emoji','')} Using *{pinfo.get('name','')}*\n\nWhat would you like to do?",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb_main(),
        )

# ─── Error Handler ────────────────────────────────────────────────────────────
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}", exc_info=context.error)

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Build HTTPXRequest with proxy + timeout support
    request_kwargs = {
        "connect_timeout": CONNECT_TIMEOUT,
        "read_timeout":    READ_TIMEOUT,
        "write_timeout":   WRITE_TIMEOUT,
        "pool_timeout":    POOL_TIMEOUT,
    }
    if PROXY_URL:
        request_kwargs["proxy"] = PROXY_URL
        print(f"  🔀  Proxy: {PROXY_URL}")

    request = HTTPXRequest(**request_kwargs)

    builder = Application.builder().token(TELEGRAM_TOKEN).request(request)
    app = builder.build()

    for cmd, handler in [
        ("start",     cmd_start),
        ("help",      cmd_help),
        ("clear",     cmd_clear),
        ("about",     cmd_about),
        ("ai",        cmd_ai),
        ("draw",      cmd_draw),
        ("translate", cmd_translate),
        ("summarize", cmd_summarize),
        ("code",      cmd_code),
        ("style",     cmd_style),
    ]:
        app.add_handler(CommandHandler(cmd, handler))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_error_handler(error_handler)

    print("  ✅  Bot started! Press Ctrl+C to stop.")
    print("  💡  If you get timeout errors, set PROXY_URL in config.py\n")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
