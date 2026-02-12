import os
import time
import threading
import requests
import telebot
import instaloader
import gradio as gr

# --- CONFIGURATION ---
# Render automatically provides the PORT variable.
# We default to 7860 only for local testing.
PORT = int(os.environ.get("PORT", 7860))

# Get Secrets (Make sure these are set in Render Environment Variables)
API_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", 952566298))

# --- DIAGNOSTIC: CHECK INTERNET ---
print("🔍 DIAGNOSTIC: Testing Connection...")
try:
    requests.get("https://google.com", timeout=5)
    print("✅ Google Reachable (Internet OK)")
    requests.get("https://api.telegram.org", timeout=5)
    print("✅ Telegram API Reachable")
except Exception as e:
    print(f"⚠️ WARNING: Network check failed: {e}")
    # We continue anyway because sometimes specific pings fail but the bot still works.

# --- INITIALIZE BOT ---
if not API_TOKEN:
    print("❌ FATAL: BOT_TOKEN is missing! Check Render Environment Variables.")
    exit(1)

bot = telebot.TeleBot(API_TOKEN)
L = instaloader.Instaloader()

# --- BOT LOGIC ---
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    print(f"📩 Message from {message.from_user.id}: {message.text}")

    # Security Check
    if message.from_user.id != ALLOWED_USER_ID:
        print(f"⛔ Blocked unauthorized user: {message.from_user.id}")
        return

    text = message.text.strip()
    
    # Check for Link
    if "instagram.com" not in text:
        bot.reply_to(message, "👋 Send me a valid Instagram Reel link!")
        return

    msg = bot.reply_to(message, "⏳ Processing...")

    try:
        # Extract Shortcode (robust method)
        if "/reel/" in text:
            shortcode = text.split("/reel/")[1].split("/")[0]
        elif "/p/" in text:
            shortcode = text.split("/p/")[1].split("/")[0]
        else:
            bot.edit_message_text("❌ Could not find Reel ID.", chat_id=message.chat.id, message_id=msg.message_id)
            return

        # Clean shortcode of any query params like ?igsh=...
        shortcode = shortcode.split("?")[0]

        print(f"🔎 Scraping ID: {shortcode}")
        
        # Scrape
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        caption = post.caption if post.caption else "[No caption]"
        
        # Send Result
        bot.edit_message_text(f"✅ **CAPTION:**\n\n{caption}", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        print("✅ Caption sent!")

    except Exception as e:
        error = str(e)
        print(f"❌ Error: {error}")
        bot.edit_message_text(f"❌ Error: {error}", chat_id=message.chat.id, message_id=msg.message_id)

# --- RUN LOOP ---
def start_bot():
    print("🚀 BOT STARTED")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Crash: {e}. Restarting in 5s...")
            time.sleep(5)

# --- LAUNCH ---
if __name__ == "__main__":
    # 1. Start Bot in Background Thread
    t = threading.Thread(target=start_bot)
    t.start()

    # 2. Start Web Server (Required by Render to keep app alive)
    # We bind to 0.0.0.0 and the correct PORT
    with gr.Blocks() as demo:
        gr.Markdown("## 🤖 Instagram Bot Running")
        gr.Markdown(f"Listening on Port: {PORT}")
        gr.Markdown(f"Allowed User: {ALLOWED_USER_ID}")
    
    demo.launch(server_name="0.0.0.0", server_port=PORT)
