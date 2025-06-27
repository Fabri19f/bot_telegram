from __future__ import annotations

import logging
import os
from pathlib import Path
from textwrap import dedent

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import google.generativeai as genai

# 1. Configuración
load_dotenv()
TG_TOKEN   = os.getenv("api_telegram")
GEMINI_KEY = os.getenv("api_gemini")

if not TG_TOKEN or not GEMINI_KEY:
    raise RuntimeError("Faltan api_telegram o api_gemini en .env")

genai.configure(api_key=GEMINI_KEY)
MODEL = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

BASE_DIR     = Path(__file__).resolve().parent
TRAINING_TXT = (BASE_DIR / "training.txt").read_text(encoding="utf-8")

# 2. Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = dedent(
        """
        *¡Hola!* Soy tu asistente de **programación competitiva**.
        
        Escríbeme cualquier pregunta y responderé en un máximo de _tres párrafos_
        con la información más relevante.
        """
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# 3. Chat principal
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_msg = update.message.text

    prompt = f"""{TRAINING_TXT}

Pregunta del usuario: {user_msg}
Responde en español, en un *máximo de tres párrafos* (≤ 4 000 caracteres).
El código debe estar en inglés y seguir buenas prácticas."""

    try:
        reply = MODEL.generate_content(prompt).text.strip()
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception as exc:
        logging.exception(exc)
        await update.message.reply_text(
            "Lo siento, ocurrió un error. Intenta nuevamente.",
            parse_mode=ParseMode.MARKDOWN,
        )

# 4. Bootstrap
def main() -> None:
    app = ApplicationBuilder().token(TG_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    logging.info("Bot iniciado…")
    app.run_polling()


if __name__ == "__main__":
    main()
