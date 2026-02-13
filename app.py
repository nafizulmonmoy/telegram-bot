import os
import time
import threading
import requests
import telebot
import instaloader
import yt_dlp
import gradio as gr

# --- CONFIGURATION ---
PORT = int(os.environ.get("PORT", 7860))
API_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_USER_ID = int(os.environ.get("ALLOWED_USER_ID", 952566298))

# --- DIAGNOSTIC ---
print("🔍 DIAGNOSTIC: Testing Connection...")
try:
    requests.get("https://google.com", timeout=5)
    requests.get("https://api.telegram.org", timeout=5)
    print("✅ Network OK")
except Exception as e:
    print(f"⚠️ Network check warning: {e}")

if not API_TOKEN:
    print("❌ FATAL: BOT_TOKEN is missing!")
    exit(1)

# --- INITIALIZE TOOLS ---
bot = telebot.TeleBot(API_TOKEN)
L = instaloader.Instaloader()

# --- BOT LOGIC ---
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    if message.from_user.id != ALLOWED_USER_ID:
        return

    text = message.text.strip()
    print(f"📩 Link received: {text}")

    # ROUTE 1: INSTAGRAM
    if "instagram.com" in text:
        msg = bot.reply_to(message, "⏳ Processing Instagram...")
        try:
            if "/reel/" in text:
                shortcode = text.split("/reel/")[1].split("/")[0]
            elif "/p/" in text:
                shortcode = text.split("/p/")[1].split("/")[0]
            else:
                bot.edit_message_text("❌ Could not find IG Reel ID.", chat_id=message.chat.id, message_id=msg.message_id)
                return

            shortcode = shortcode.split("?")[0]
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            caption = post.caption if post.caption else "[No caption]"
            
            bot.edit_message_text(f"✅ **IG CAPTION:**\n\n{caption}", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

        except Exception as e:
            bot.edit_message_text(f"❌ IG Error: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

    # ROUTE 2: FACEBOOK
    elif "facebook.com" in text or "fb.watch" in text or "fb.video" in text:
        msg = bot.reply_to(message, "⏳ Processing Facebook...")
        try:
            # yt-dlp extracts the metadata without downloading the heavy video file
            ydl_opts = {'quiet': True, 'extract_flat': False} 
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(text, download=False)
                
                # Facebook sometimes stores the caption in 'description', sometimes in 'title'
                caption = info.get('description') or info.get('title') or "[No caption found]"
                
            bot.edit_message_text(f"✅ **FB CAPTION:**\n\n{caption}", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

        except Exception as e:
            bot.edit_message_text(f"❌ FB Error: {str(e)}", chat_id=message.chat.id, message_id=msg.message_id)

    # UNKNOWN LINK
    else:
        bot.reply_to(message, "👋 Send me a valid Instagram or Facebook link!")

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
    t = threading.Thread(target=start_bot)
    t.start()

    with gr.Blocks() as demo:
        gr.Markdown("## 🤖 Multi-Platform Bot Running")
        gr.Markdown(f"Listening on Port: {PORT}")
    
    demo.launch(server_name="0.0.0.0", server_port=PORT)
