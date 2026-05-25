import telebot
import sqlite3
import os
from flask import Flask
from threading import Thread

# Flask সার্ভার (বটকে সচল রাখতে)
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# আপনার তথ্য
TOKEN = '8989199216:AAE2FvkRf4t78a5Jk8JZ-fFQcW3zCQ8bvn0' # আপনার টোকেনটি এখানে দিন
bot = telebot.TeleBot(TOKEN)
ADMIN_USERNAME = "@Rakib4545" # আপনার ইউজারনেম

# ডাটাবেজ সেটআপ
def get_db_connection():
    conn = sqlite3.connect('earning.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id TEXT PRIMARY KEY, balance REAL, referred_by TEXT, daily_claimed INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# বাটন কিবোর্ড
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('💰 Balance', '🎁 Daily Bonus')
    markup.add('👥 Refer & Earn', '💳 Withdraw')
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    user_id = str(message.chat.id)
    text_split = message.text.split()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        referrer_id = None
        if len(text_split) > 1:
            ref_candidate = text_split[1]
            if ref_candidate != user_id:
                referrer_id = ref_candidate
                cursor.execute("UPDATE users SET balance = balance + 5.0 WHERE user_id = ?", (referrer_id,))
                try:
                    bot.send_message(referrer_id, "🎉 কেউ আপনার লিঙ্কে জয়েন করেছে! আপনি ৫ টাকা পেয়েছেন।")
                except: pass
        
        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (user_id, 0.0, referrer_id, 0))
        conn.commit()
    
    conn.close()
    bot.send_message(user_id, "স্বাগতম! কাজ শুরু করুন।", reply_markup=main_menu())

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    user_id = str(message.chat.id)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if message.text == '💰 Balance':
        bot.send_message(user_id, f"💵 ব্যালেন্স: {data[1]} টাকা")
    elif message.text == '🎁 Daily Bonus':
        if data[3] == 0:
            cursor.execute("UPDATE users SET balance = balance + 2.0, daily_claimed = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            bot.send_message(user_id, "✅ ২ টাকা বোনাস পেয়েছেন!")
        else:
            bot.send_message(user_id, "❌ আজ নেওয়া শেষ।")
    elif message.text == '👥 Refer & Earn':
        bot_username = bot.get_me().username
        bot.send_message(user_id, f"🔗 রেফার লিঙ্ক: https://t.me/{bot_username}?start={user_id}")
    elif message.text == '💳 Withdraw':
        if data[1] >= 50:
            bot.send_message(user_id, f"💸 উইথড্রর জন্য অ্যাডমিনকে মেসেজ দিন: {ADMIN_USERNAME}")
        else:
            bot.send_message(user_id, "❌ সর্বনিম্ন ৫০ টাকা লাগে।")
    conn.close()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
