import telebot
import sqlite3
from flask import Flask
from threading import Thread
import time

# ১. আপনার তথ্য
TOKEN = '8989199216:AAE2FvkRf4t78a5Jk8JZ-fFQc'
bot = telebot.TeleBot(TOKEN)
ADMIN_USERNAME = "@Rakib4545"

# ২. টাস্ক লিস্ট
tasks = [
    {
        'id': 1,
        'text': '🔥 ১০০ পয়েন্ট বোনাস পেতে নিচের লিঙ্কে ক্লিক করে ১০ সেকেন্ড অপেক্ষা করুন',
        'link': 'https://shrinkme.click/2NfYmRso',
        'reward': 100
    },
    {
        'id': 2,
        'text': '✅ এই সহজ অফারটি পূরণ করে ২০০ পয়েন্ট নিন',
        'link': 'https://singingfiles.com/show.php?l=0&u=2529780&id=36521',
        'reward': 200
    }
]

# ৩. ডাটাবেজ সেটআপ
def get_db_connection():
    return sqlite3.connect('earning.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                     (user_id TEXT PRIMARY KEY, balance REAL, referred_by TEXT, daily_claimed INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# ৪. বাটন কিবোর্ড
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add('💰 Balance', '🎁 Daily Bonus')
    markup.add('👥 Refer & Earn', '📋 Tasks')
    markup.add('💳 Withdraw')
    return markup

# ৫. স্টার্ট কমান্ড হ্যান্ডলার
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
    bot.send_message(user_id, "স্বাগতম! আমাদের বট থেকে কাজ করে প্রতিদিন টাকা আয় করুন।", reply_markup=main_menu())

# ৬. মেসেজ হ্যান্ডলার (বাটন ছাড়া অন্য মেসেজ আসলে ডিলিট হবে)
@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    user_id = str(message.chat.id)
    text = message.text
    valid_buttons = ['💰 Balance', '🎁 Daily Bonus', '👥 Refer & Earn', '📋 Tasks', '💳 Withdraw']

    # যদি মেসেজটি বাটন লিস্টে না থাকে, তবে সেটি ডিলিট করে দাও
    if text not in valid_buttons:
        try:
            bot.delete_message(user_id, message.message_id)
            # ইউজারকে সতর্ক করার জন্য একটি মেসেজ পাঠিয়ে ২ সেকেন্ড পর সেটিও ডিলিট করে দেওয়া যেতে পারে
            warning = bot.send_message(user_id, "❌ শুধু বাটন ব্যবহার করুন! অন্য মেসেজ দেওয়া নিষেধ।")
            time.sleep(2)
            bot.delete_message(user_id, warning.message_id)
        except:
            pass
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if not data:
        bot.send_message(user_id, "অনুগ্রহ করে /start লিখুন।")
        return

    if text == '💰 Balance':
        bot.send_message(user_id, f"💵 আপনার বর্তমান ব্যালেন্স: {data[1]} টাকা")
    
    elif text == '📋 Tasks':
        bot.send_message(user_id, "👇 নিচের টাস্কগুলো সম্পন্ন করে আয় করুন:")
        for task in tasks:
            task_text = f"📝 {task['text']}\n🔗 লিঙ্ক: {task['link']}\n🎁 পুরস্কার: {task['reward']} পয়েন্ট"
            bot.send_message(user_id, task_text)
            
    elif text == '🎁 Daily Bonus':
        if data[3] == 0:
            cursor.execute("UPDATE users SET balance = balance + 2.0, daily_claimed = 1 WHERE user_id = ?", (user_id,))
            conn.commit()
            bot.send_message(user_id, "✅ আপনি আজকের ২ টাকা বোনাস পেয়েছেন!")
        else:
            bot.send_message(user_id, "❌ আপনি আজ অলরেডি বোনাস নিয়েছেন।")
            
    elif text == '👥 Refer & Earn':
        bot_username = bot.get_me().username
        refer_link = f"https://t.me/{bot_username}?start={user_id}"
        bot.send_message(user_id, f"👥 প্রতি রেফারে পাবেন ৫ টাকা।\n🔗 আপনার রেফার লিঙ্ক: {refer_link}")
        
    elif text == '💳 Withdraw':
        if data[1] >= 50:
            bot.send_message(user_id, f"💸 উইথড্র করার জন্য আপনার তথ্যসহ অ্যাডমিনকে মেসেজ দিন: {ADMIN_USERNAME}")
        else:
            bot.send_message(user_id, f"❌ সর্বনিম্ন ৫০ টাকা প্রয়োজন। আপনার ব্যালেন্স: {data[1]} টাকা")

    conn.close()

# ৭. রেন্ডার সার্ভার
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
