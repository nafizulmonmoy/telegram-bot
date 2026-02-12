import os
import time
import threading
import requests
import telebot
import instaloader
import gradio as gr

# --- CONFIGURATION ---
# Ensure your secret is named 'BOT_TOKEN'
API_TOKEN = os.environ.get("BOT_TOKEN")
ALLOWED_USER_ID = 952566298

# --- DIAGNOSTIC: CHECK INTERNET ---
print("🔍 DIAGNOSTIC: Testing Connection...")
try:
    # Test 1: Can we reach the outside world?
    requests.get("https://google.com", timeout=5)
    print("✅ Google Reachable (Internet OK)")
    
    # Test 2: Can we reach Telegram?
    # We use verify=False to avoid SSL certificate errors on some cloud containers
    requests.get("https://api.telegram.org", timeout=5)
    print("✅ Telegram API Reachable")
except Exception as e:
    print(f"❌ CONNECTION ERROR: {e}")

# --- INITIALIZE BOT ---
bot = telebot.TeleBot(API_TOKEN)
L = instaloader.Instaloader()

# --- BOT LOGIC ---
@bot.message_handler(func=lambda m: True)
def handle_message(message):
    # Log that we received something
    print(f"📩 Message from {message.from_user.id}: {message.text}")

    if message.from_user.id != ALLOWED_USER_ID:
        return

    text = message.text.strip()
    
    if "instagram.com" not in text:
        bot.reply_to(message, "👋 Send me a valid Instagram Reel link!")
        return

    msg = bot.reply_to(message, "⏳ Processing...")

    try:
        # Extract Shortcode
        if "/reel/" in text:
            shortcode = text.split("/reel/")[1].split("/")[0]
        elif "/p/" in text:
            shortcode = text.split("/p/")[1].split("/")[0]
        else:
            bot.edit_message_text("❌ Could not find Reel ID.", chat_id=message.chat.id, message_id=msg.message_id)
            return

        print(f"🔎 Scrapping ID: {shortcode}")
        
        # Scrape
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        caption = post.caption if post.caption else "[No caption]"
        
        bot.edit_message_text(f"✅ **CAPTION:**\n\n{caption}", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        print("✅ Caption sent!")

    except Exception as e:
        error = str(e)
        print(f"❌ Error: {error}")
        bot.edit_message_text(f"❌ Error: {error}", chat_id=message.chat.id, message_id=msg.message_id)

# --- RUN LOOP ---
def start_bot():
    print("🚀 BOT STARTED (HTTP MODE)")
    while True:
        try:
            bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ Crash: {e}. Restarting in 5s...")
            time.sleep(5)

# --- LAUNCH ---
if __name__ == "__main__":
    # Start Bot in Background
    t = threading.Thread(target=start_bot)
    t.start()

    # Start Web Server
    with gr.Blocks() as demo:
        gr.Markdown("## 🤖 HTTP Caption Bot Online")
        gr.Markdown(f"Current User ID: `{ALLOWED_USER_ID}`")
    demo.launch(server_name="0.0.0.0", server_port=7860)