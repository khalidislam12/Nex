# -*- coding: utf-8 -*-
import telebot
from telebot import types
import sqlite3
from datetime import datetime

# 🛑 কনফিগারেশন (আপনার আসল টোকেন ও আইডি দিন)
BOT_TOKEN = "8950916305:AAGXL98WYGh6OjhrQgX7i5F5KkbNpA9YLZs"   
OWNER_ID = 8340080753  # বটের মূল মালিক (Super Admin) এর আইডি

bot = telebot.TeleBot(BOT_TOKEN)

# 💾 ডাটাবেজ সেটআপ
def init_db():
    conn = sqlite3.connect('meme_nex_shop_v7.db')
    cursor = conn.cursor()
    
    # ইউজার টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance REAL DEFAULT 0.0,
        total_deposit REAL DEFAULT 0.0,
        total_product INTEGER DEFAULT 0,
        joined_date TEXT,
        referred_by INTEGER DEFAULT NULL,
        verified_ref_count INTEGER DEFAULT 0,
        total_ref_earnings REAL DEFAULT 0.0
    )''')
    
    # ডায়নামিক এডমিন পারমিশন টেবিল
    cursor.execute('''CREATE TABLE IF NOT EXISTS admin_permissions (
        user_id INTEGER,
        permission TEXT,
        PRIMARY KEY (user_id, permission)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT,
        price_bdt REAL,
        price_usdt REAL,
        file_id TEXT,
        photo_url TEXT,
        FOREIGN KEY(category_id) REFERENCES categories(id)
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_name TEXT,
        file_id TEXT,
        purchase_date TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS force_channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_id TEXT UNIQUE,
        invite_link TEXT,
        type TEXT DEFAULT 'channel'
    )''')
    
    # ৩টি আলাদা আলাদা নোটিফিকেশন চ্যানেলের জন্য টেবিল স্ট্রাকচার পরিবর্তন করা হয়েছে
    cursor.execute('''CREATE TABLE IF NOT EXISTS notify_chats (
        chat_type TEXT PRIMARY KEY,
        chat_id TEXT,
        chat_name TEXT
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    
    default_settings = [
        ('support_link', 'https://t.me/dxazone_support'),
        ('dev_link', 'https://t.me/dxa_developer'),
        ('shop_link', f'https://t.me/NEX_PAID_SHOP_BOT?start=shop'),
        ('min_deposit_bdt', '50'),
        ('min_deposit_usdt', '1'),
        ('usdt_rate', '135'), # ১ USDT = কত টাকা (এডমিন যখন যা দিবে সেটা শো করবে)
        ('status_bkash', 'ON'),
        ('status_nagad', 'ON'),
        ('status_rocket', 'ON'),
        ('status_binance', 'ON'),
        ('bkash_num', '017XXXXXXXX'),
        ('nagad_num', '019XXXXXXXX'),
        ('rocket_num', '015XXXXXXXX'),
        ('binance_pay', '123456789'),
        ('emo_buy', '🛍'),
        ('emo_dep', '💳'),
        ('emo_ref', '🎁'),
        ('emo_ord', '📦'),
        ('emo_acc', '👤'),
        ('emo_sup', '💬'),
        ('emo_dev', '👨‍💻')
    ]
    cursor.executemany('INSERT OR IGNORE INTO settings VALUES (?, ?)', default_settings)
    conn.commit()
    conn.close()

init_db()

# ⚙️ ডাটাবেজ হেল্পার
def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('meme_nex_shop_v7.db')
    cursor = conn.cursor()
    cursor.execute(query, params)
    res = None
    if fetchone: res = cursor.fetchone()
    if fetchall: res = cursor.fetchall()
    if commit: conn.commit()
    conn.close()
    return res

# 🛡️ পারমিশন চেক
def has_permission(user_id, permission):
    if user_id == OWNER_ID: return True
    res = db_query("SELECT 1 FROM admin_permissions WHERE user_id=? AND permission=?", (user_id, permission), fetchone=True)
    return res is not None

def is_any_admin(user_id):
    if user_id == OWNER_ID: return True
    res = db_query("SELECT 1 FROM admin_permissions WHERE user_id=?", (user_id,), fetchone=True)
    return res is not None

# 🛡️ ফোর্স জয়েন ভেরিফিকেশন (সবগুলো চ্যানেল চেক করবে)
def is_user_joined(user_id):
    channels = db_query("SELECT channel_id FROM force_channels", fetchall=True)
    if not channels: return True
    for ch in channels:
        try:
            member = bot.get_chat_member(ch[0], user_id)
            if member.status in ['left', 'kicked']: return False
        except Exception: return False
    return True

def force_join_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    channels = db_query("SELECT invite_link, type FROM force_channels", fetchall=True)
    for i, ch in enumerate(channels, start=1):
        icon = "📢" if ch[1] == 'channel' else "👥"
        markup.add(types.InlineKeyboardButton(f"{icon} Join Channel/Group {i}", url=ch[0]))
    markup.add(types.InlineKeyboardButton("🔄 Check Membership", callback_data="check_join"))
    return markup

def main_keyboard():
    e_buy = db_query("SELECT value FROM settings WHERE key='emo_buy'", fetchone=True)[0]
    e_dep = db_query("SELECT value FROM settings WHERE key='emo_dep'", fetchone=True)[0]
    e_ref = db_query("SELECT value FROM settings WHERE key='emo_ref'", fetchone=True)[0]
    e_ord = db_query("SELECT value FROM settings WHERE key='emo_ord'", fetchone=True)[0]
    e_acc = db_query("SELECT value FROM settings WHERE key='emo_acc'", fetchone=True)[0]
    e_sup = db_query("SELECT value FROM settings WHERE key='emo_sup'", fetchone=True)[0]
    e_dev = db_query("SELECT value FROM settings WHERE key='emo_dev'", fetchone=True)[0]

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton(f"{e_buy} BUY SHOP PRODUCT"),
        types.KeyboardButton(f"{e_dep} DEPOSIT MONEY"),
        types.KeyboardButton(f"{e_ref} REFER"),
        types.KeyboardButton(f"{e_ord} MY ORDERS"),
        types.KeyboardButton(f"{e_acc} MY ACCOUNT"),
        types.KeyboardButton(f"{e_sup} SUPPORT"),
        types.KeyboardButton(f"{e_dev} DEVELOPER")
    )
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "No Username"
    first_name = message.from_user.first_name
    
    referred_by = None
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit() and int(args[1]) != user_id:
        referred_by = int(args[1])

    user_exists = db_query("SELECT user_id FROM users WHERE user_id=?", (user_id,), fetchone=True)
    if not user_exists:
        joined_date = datetime.now().strftime("%Y-%m-%d")
        db_query("INSERT INTO users (user_id, username, first_name, joined_date, referred_by) VALUES (?, ?, ?, ?, ?)",
                 (user_id, username, first_name, joined_date, referred_by), commit=True)
        
        # 📊 ইউজার কত নাম্বার ফিউচার মেম্বার তা গণনা করা
        user_count = db_query("SELECT COUNT(*) FROM users", fetchone=True)[0]
        
        # 🔔 ১. নিউ ইউজার ওয়েলকাম নোটিফিকেশন ফরোয়ার্ড
        welcome_chat = db_query("SELECT chat_id FROM notify_chats WHERE chat_type='user_join'", fetchone=True)
        if welcome_chat:
            welcome_msg = f"╭─────────────────────╮\n" \
                          f"   👋 <b>New User Joined Bot!</b>\n" \
                          f"╰─────────────────────╯\n" \
                          f"👤 <b>Name:</b> {first_name}\n" \
                          f"🆔 <b>User ID:</b> <code>{user_id}</code>\n" \
                          f"🏷 <b>Username:</b> {username}\n" \
                          f"🔢 <b>Member Serial:</b> {user_count}th Member\n" \
                          f"📅 <b>Date:</b> {joined_date}\n" \
                          f"📌 <b>Status:</b> Welcome Message Dispatched! 🎉\n" \
                          f"──────────────────────"
            try: bot.send_message(welcome_chat[0], welcome_msg, parse_mode="HTML")
            except Exception: pass

        if referred_by:
            try: bot.send_message(referred_by, f"🎁 <b>নতুন মেম্বার আপনার আমন্ত্রণে বটের সাথে যুক্ত হয়েছে!</b>", parse_mode="HTML")
            except Exception: pass

    if not is_user_joined(user_id):
        welcome_premium = f"╭─────────────────────╮\n" \
                          f"   ⚠️ <b>JOINING REQUIRED!</b>\n" \
                          f"╰─────────────────────╯\n" \
                          f"বটের সমস্ত সার্ভিস বা প্রোডাক্ট অ্যাক্সেস করতে আপনাকে প্রথমে নিচের সকল চ্যানেল বা গ্রুপে যুক্ত হতে হবে।\n\n" \
                          f"🔗 সবগুলো চ্যানেলে যুক্ত হয়ে <b>Membership Check</b> বাটনে ক্লিক করুন।"
        bot.send_message(user_id, welcome_premium, reply_markup=force_join_keyboard(), parse_mode="HTML")
        return

    premium_start = f"╭─────────────────────╮\n" \
                    f"   ✨ <b>WELCOME TO NEX PAID SHOP</b>\n" \
                    f"╰─────────────────────╯\n" \
                    f"হ্যালো, <b>{first_name}</b>! আমাদের প্রিমিয়াম সপ বটে আপনাকে স্বাগতম। নিচে দেওয়া বাটনগুলো থেকে আপনার প্রয়োজনীয় সার্ভিসটি সিলেক্ট করুন।"
    bot.send_message(user_id, premium_start, reply_markup=main_keyboard(), parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_join")
def check_join_callback(call):
    if is_user_joined(call.from_user.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "🎉 <b>ভেরিফিকেশন সফল! আপনার সমস্ত ফিচার আনলক করা হয়েছে।</b>", reply_markup=main_keyboard(), parse_mode="HTML")
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো সবগুলো চ্যানেল বা গ্রুপে জয়েন করেননি! দয়া করে সবগুলোতে জয়েন করুন।", show_alert=True)

# 🛍 প্রোডাক্ট শপ সেকশন ও ক্রয় নোটিফিকেশন
@bot.message_handler(func=lambda m: m.text and ("BUY SHOP PRODUCT" in m.text))
def buy_shop_product(message):
    if not is_user_joined(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ আগে জয়েন করুন!", reply_markup=force_join_keyboard())
        return
    categories = db_query("SELECT id, name FROM categories", fetchall=True)
    markup = types.InlineKeyboardMarkup(row_width=1)
    for cat_id, name in categories:
        stock = db_query("SELECT COUNT(*) FROM products WHERE category_id=?", (cat_id,), fetchone=True)[0]
        markup.add(types.InlineKeyboardButton(f"📁 {name} [Stock: {stock}]", callback_data=f"cat_{cat_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Back To Home", callback_data="go_home"))
    
    premium_text = f"╭─────────────────────╮\n" \
                   f"   🛒 <b>PRODUCT CATEGORIES</b>\n" \
                   f"╰─────────────────────╯\n" \
                   f"আপনার কাঙ্ক্ষিত ক্যাটাগরিটি নিচের লিস্ট থেকে সিলেক্ট করুন:"
    bot.send_message(message.chat.id, premium_text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
def show_products(call):
    cat_id = call.data.split('_')[1]
    products = db_query("SELECT id, name, price_bdt, price_usdt FROM products WHERE category_id=?", (cat_id,), fetchall=True)
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # এডমিনের সেট করা রেট লোড করা
    rate = float(db_query("SELECT value FROM settings WHERE key='usdt_rate'", fetchone=True)[0])
    
    for p_id, name, p_bdt, p_usdt in products:
        # রেট অনুযায়ী লাইভ USDT কনভার্ট
        calc_usdt = p_bdt / rate
        markup.add(types.InlineKeyboardButton(f"💥 {name} - ৳{p_bdt:.2f} BDT ({calc_usdt:.2f} USDT)", callback_data=f"prod_{p_id}"))
    markup.add(types.InlineKeyboardButton("⬅️ Back to Categories", callback_data="back_to_shop"))
    
    premium_text = f"╭─────────────────────╮\n" \
                   f"   🛒  <b>AVAILABLE PRODUCTS</b>\n" \
                   f"╰─────────────────────╯\n" \
                   f"ক্রয় করার জন্য যেকোনো একটি প্রোডাক্টের ওপর ক্লিক করুন:"
    bot.edit_message_text(premium_text, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('prod_'))
def product_details(call):
    p_id = call.data.split('_')[1]
    product = db_query("SELECT id, name, price_bdt, price_usdt, photo_url FROM products WHERE id=?", (p_id,), fetchone=True)
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    rate = float(db_query("SELECT value FROM settings WHERE key='usdt_rate'", fetchone=True)[0])
    calc_usdt = product[2] / rate
    
    markup.add(
        types.InlineKeyboardButton(f"💳 Purchase Now (৳{product[2]:.2f})", callback_data=f"confirm_buy_{product[0]}"),
        types.InlineKeyboardButton("🖼 View Product Demo Image", url=product[4]),
        types.InlineKeyboardButton("⬅️ Back to Shop List", callback_data="back_to_shop")
    )
    desc = f"╭─────────────────────╮\n" \
           f"   📦 <b>PRODUCT DETAILS INFO</b>\n" \
           f"╰─────────────────────╯\n" \
           f"📝 <b>Name:</b> {product[1]}\n" \
           f"💰 <b>Price BDT:</b> ৳{product[2]:.2f} BDT\n" \
           f"🪙 <b>Price USDT:</b> {calc_usdt:.2f} USDT\n" \
           f"📊 <b>Current Exchange Rate:</b> 1 USDT = {rate} BDT\n" \
           f"──────────────────────"
    bot.edit_message_text(desc, call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_buy_'))
def confirm_purchase(call):
    p_id = call.data.split('_')[2]
    user_id = call.from_user.id
    
    user_data = db_query("SELECT balance, first_name FROM users WHERE user_id=?", (user_id,), fetchone=True)
    user_balance, f_name = user_data[0], user_data[1]
    
    product = db_query("SELECT name, price_bdt, price_usdt, file_id FROM products WHERE id=?", (p_id,), fetchone=True)
    prod_name, price_bdt, price_usdt, file_id = product[0], product[1], product[2], product[3]
    
    rate = float(db_query("SELECT value FROM settings WHERE key='usdt_rate'", fetchone=True)[0])
    # সমস্ত হিসাব USDT অনুযায়ী চলবে
    required_usdt = price_bdt / rate
    
    if user_balance >= required_usdt:
        new_balance = user_balance - required_usdt
        db_query("UPDATE users SET balance=?, total_product=total_product+1 WHERE user_id=?", (new_balance, user_id), commit=True)
        p_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        db_query("INSERT INTO purchases (user_id, product_name, file_id, purchase_date) VALUES (?, ?, ?, ?)", (user_id, prod_name, file_id, p_date), commit=True)
        
        bot.answer_callback_query(call.id, "🎉 Purchase Successful!", show_alert=True)
        bot.send_message(user_id, f"✅ <b>ক্রয় সফল হয়েছে! নিচে আপনার প্রিমিয়াম ফাইল দেওয়া হলো:</b>", parse_mode="HTML")
        try: bot.send_document(user_id, file_id)
        except Exception: pass
        
        shop_url = db_query("SELECT value FROM settings WHERE key='shop_link'", fetchone=True)[0]
        support_url = db_query("SELECT value FROM settings WHERE key='support_link'", fetchone=True)[0]
        dev_url = db_query("SELECT value FROM settings WHERE key='dev_link'", fetchone=True)[0]
        e_buy = db_query("SELECT value FROM settings WHERE key='emo_buy'", fetchone=True)[0]
        e_sup = db_query("SELECT value FROM settings WHERE key='emo_sup'", fetchone=True)[0]
        e_dev = db_query("SELECT value FROM settings WHERE key='emo_dev'", fetchone=True)[0]

        group_markup = types.InlineKeyboardMarkup()
        group_markup.row(types.InlineKeyboardButton(f"{e_buy} SHOP", url=shop_url), types.InlineKeyboardButton(f"{e_sup} SUPPORT", url=support_url))
        group_markup.row(types.InlineKeyboardButton(f"{e_dev} DEVELOPER", url=dev_url))

        # 🔔 ২. পারচেজ নোটিফিকেশন চ্যানেল ফরোয়ার্ড
        purchase_chat = db_query("SELECT chat_id FROM notify_chats WHERE chat_type='purchase'", fetchone=True)
        if purchase_chat:
            purchase_alert = f"╭─────────────────────╮\n" \
                             f"   🛍️ <b>PRODUCT PURCHASED!</b>\n" \
                             f"╰─────────────────────╯\n" \
                             f"👤 <b>User:</b> {f_name}\n" \
                             f"🆔 <b>User ID:</b> <code>{user_id}</code>\n" \
                             f"📦 <b>Product:</b> {prod_name}\n" \
                             f"💰 <b>Amount BDT:</b> ৳{price_bdt:.2f} BDT\n" \
                             f"🪙 <b>Amount USDT:</b> {required_usdt:.2f} USDT\n" \
                             f"📅 <b>Date:</b> {p_date}\n" \
                             f"⚡ <b>Delivery Status:</b> Automated Instant Success ✅\n" \
                             f"──────────────────────"
            try: bot.send_message(purchase_chat[0], purchase_alert, reply_markup=group_markup, parse_mode="HTML")
            except Exception: pass
    else:
        bot.answer_callback_query(call.id, f"❌ আপনার একাউন্টে পর্যাপ্ত ব্যালেন্স নেই! প্রয়োজন: {required_usdt:.2f} USDT", show_alert=True)

# 💳 ডিপোজিট সেকশন
@bot.message_handler(func=lambda m: m.text and ("DEPOSIT MONEY" in m.text))
def deposit_money(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🇧🇩 BDT (Mobile Banking)", callback_data="init_bdt"), types.InlineKeyboardButton("🪙 USDT (Crypto Pay)", callback_data="init_usdt"))
    
    rate = db_query("SELECT value FROM settings WHERE key='usdt_rate'", fetchone=True)[0]
    premium_text = f"╭─────────────────────╮\n" \
                   f"   💳 <b>SECURE DEPOSIT CENTER</b>\n" \
                   f"╰─────────────────────╯\n" \
                   f"ব্যালেন্স অ্যাড করতে আপনার কাঙ্ক্ষিত মেথড কারেন্সি সিলেক্ট করুন:\n\n" \
                   f"📊 <b>Current Rate:</b> 1 USDT = {rate} BDT\n" \
                   f"🔐 সমস্ত ফান্ড সয়ংক্রিয়ভাবে USDT-তে কনভার্ট হয়ে ওয়ালেটে জমা হবে।"
    bot.send_message(message.chat.id, premium_text, reply_markup=markup, parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data in ['init_bdt', 'init_usdt'])
def ask_deposit_amount(call):
    currency = "BDT" if call.data == 'init_bdt' else "USDT"
    min_amt = db_query(f"SELECT value FROM settings WHERE key='min_deposit_{currency.lower()}'", fetchone=True)[0]
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    msg = bot.send_message(call.message.chat.id, f"📥 <b>সর্বনিম্ন ডিপোজিট পরিমাণ: {min_amt} {currency}</b>\n\nআপনি কত ডিপোজিট করতে চান তা সংখ্যায় লিখুন (যেমন: ১০০):", parse_mode="HTML")
    bot.register_next_step_handler(msg, process_amount_and_show_gateways, currency, float(min_amt))

def process_amount_and_show_gateways(message, currency, min_amt):
    try:
        amount = float(message.text.strip())
        if amount < min_amt:
            bot.send_message(message.chat.id, "❌ <b>দুঃখিত! সর্বনিম্ন ডিপোজিট লিমিটের নিচের পরিমাণ গ্রহণযোগ্য নয়।</b>", parse_mode="HTML")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        if currency == "BDT":
            if db_query("SELECT value FROM settings WHERE key='status_bkash'", fetchone=True)[0] == 'ON':
                markup.add(types.InlineKeyboardButton("📱 bKash Personal", callback_data=f"pay_BKASH_{amount}"))
            if db_query("SELECT value FROM settings WHERE key='status_nagad'", fetchone=True)[0] == 'ON':
                markup.add(types.InlineKeyboardButton("📱 Nagad Personal", callback_data=f"pay_NAGAD_{amount}"))
            if db_query("SELECT value FROM settings WHERE key='status_rocket'", fetchone=True)[0] == 'ON':
                markup.add(types.InlineKeyboardButton("📱 Rocket Personal", callback_data=f"pay_ROCKET_{amount}"))
        else:
            if db_query("SELECT value FROM settings WHERE key='status_binance'", fetchone=True)[0] == 'ON':
                markup.add(types.InlineKeyboardButton("🔶 Binance Pay ID / USDT-TRC20", callback_data=f"pay_BINANCE_{amount}"))
        
        bot.send_message(message.chat.id, f"⚡ <b>ডিপোজিট সম্পন্ন করতে নিচের পেমেন্ট গেটওয়েটি সিলেক্ট করুন:</b>", reply_markup=markup, parse_mode="HTML")
    except ValueError:
        bot.send_message(message.chat.id, "❌ <b>ভুল ইনপুট! দয়া করে শুধুমাত্র সংখ্যায় পরিমাণটি লিখুন।</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith('pay_'))
def show_payment_address(call):
    _, method, amount = call.data.split('_')
    setting_key = f"{method.lower()}_num" if method in ['BKASH', 'NAGAD', 'ROCKET'] else "binance_pay"
    address = db_query("SELECT value FROM settings WHERE key=?", (setting_key,), fetchone=True)[0]
    bot.delete_message(call.message.chat.id, call.message.message_id)
    
    pay_instruction = f"╭─────────────────────╮\n" \
                      f"   📥 <b>{method} PAYMENT INSTRUCTION</b>\n" \
                      f"╰─────────────────────╯\n" \
                      f"📍 <b>নম্বর / অ্যাড্রেস:</b> <code>{address}</code>\n" \
                      f"💰 <b>টাকার পরিমাণ:</b> {amount}\n\n" \
                      f"⚠️ <b>নির্দেশনা:</b> উক্ত নম্বরে সফলভাবে অর্থ পাঠানোর পর, ফিরতি মেসেজে পাওয়া <b>Transaction ID (TxID)</b> বা অর্ডার প্রুফ টেক্সটটি এখানে ইনপুট দিন:"
    msg = bot.send_message(call.message.chat.id, pay_instruction, parse_mode="HTML")
    bot.register_next_step_handler(msg, submit_deposit_to_admin, method, amount)

def submit_deposit_to_admin(message, method, amount):
    tx_id = message.text.strip()
    admin_markup = types.InlineKeyboardMarkup()
    admin_markup.add(
        types.InlineKeyboardButton("✅ Approve Request", callback_data=f"apv_{message.from_user.id}_{amount}_{method}"),
        types.InlineKeyboardButton("❌ Reject Request", callback_data=f"reject_{message.from_user.id}")
    )
    db_query("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (f"tx_{message.from_user.id}", tx_id), commit=True)
    
    bot.send_message(OWNER_ID, f"🔔 <b>নতুন ডিপোজিট রিকোয়েস্ট এসেছে!</b>\n🆔 ইউজার আইডি: {message.from_user.id}\n💰 পরিমাণ: {amount} {method}\n🔑 TxID: <code>{tx_id}</code>", reply_markup=admin_markup, parse_mode="HTML")
    bot.send_message(message.chat.id, "✅ <b>আপনার ট্রানজেকশন আইডি সফলভাবে এডমিন রিভিউয়ের জন্য সাবমিট করা হয়েছে। অনুগ্রহ করে অপেক্ষা করুন!</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data.startswith(('apv_', 'reject_')))
def admin_decision(call):
    if not has_permission(call.from_user.id, "gateways"):
        bot.answer_callback_query(call.id, "❌ আপনার পেমেন্ট সেকশনে অ্যাক্সেস পারমিশন নেই!", show_alert=True)
        return
        
    data_parts = call.data.split('_')
    action, target_id = data_parts[0], int(data_parts[1])
    
    if action == 'apv':
        amount, method = float(data_parts[2]), data_parts[3]
        rate = float(db_query("SELECT value FROM settings WHERE key='usdt_rate'", fetchone=True)[0])
        
        # BDT মেথড হলে লাইভ এডমিন রেট অনুযায়ী অটো কনভার্ট হবে, আর ডিরেক্ট ক্রিপ্টো হলে ফুল এমাউন্ট অ্যাড হবে
        usdt_credit = amount / rate if method in ['BKASH', 'NAGAD', 'ROCKET'] else amount
        
        db_query("UPDATE users SET balance = balance + ?, total_deposit = total_deposit + ? WHERE user_id = ?", (usdt_credit, usdt_credit, target_id), commit=True)
        bot.send_message(target_id, f"🎉 <b>অভিনন্দন! আপনার ডিপোজিট রিকোয়েস্টটি অ্যাপ্রুভ করা হয়েছে। ওয়ালেটে {usdt_credit:.2f} USDT যোগ করা হয়েছে।</b>", parse_mode="HTML")
        
        raw_tx = db_query("SELECT value FROM settings WHERE key=?", (f"tx_{target_id}",), fetchone=True)
        tx_id = raw_tx[0] if raw_tx else "UNKNOWN"
        f_name = db_query("SELECT first_name FROM users WHERE user_id=?", (target_id,), fetchone=True)[0]
        
        shop_url = db_query("SELECT value FROM settings WHERE key='shop_link'", fetchone=True)[0]
        support_url = db_query("SELECT value FROM settings WHERE key='support_link'", fetchone=True)[0]
        dev_url = db_query("SELECT value FROM settings WHERE key='dev_link'", fetchone=True)[0]
        e_buy = db_query("SELECT value FROM settings WHERE key='emo_buy'", fetchone=True)[0]
        e_sup = db_query("SELECT value FROM settings WHERE key='emo_sup'", fetchone=True)[0]
        e_dev = db_query("SELECT value FROM settings WHERE key='emo_dev'", fetchone=True)[0]
        
        group_markup = types.InlineKeyboardMarkup()
        group_markup.row(types.InlineKeyboardButton(f"{e_buy} SHOP", url=shop_url), types.InlineKeyboardButton(f"{e_sup} SUPPORT", url=support_url))
        group_markup.row(types.InlineKeyboardButton(f"{e_dev} DEVELOPER", url=dev_url))
        
        group_alert = f"╭─────────────────────╮\n" \
                      f"   ✅ <b>DEPOSIT SUCCESS ALLERT!</b>\n" \
                      f"╰─────────────────────╯\n" \
                      f"👤 <b>User Name:</b> {f_name}\n" \
                      f"🆔 <b>User ID:</b> <code>{target_id}</code>\n" \
                      f"💰 <b>Submited Amt:</b> {amount} {method}\n" \
                      f"🪙 <b>Credited Wallet:</b> {usdt_credit:.2f} USDT\n" \
                      f"📊 <b>Calculated Rate:</b> 1 USDT = {rate} BDT\n" \
                      f"🔑 <b>TxID:</b> <code>{tx_id}</code>\n" \
                      f"⚡ <b>Wallet Status:</b> Instant Funded Success 🔥\n" \
                      f"──────────────────────"
                      
        # 🔔 ৩. ডিপোজিট নোটিফিকেশন চ্যানেল ফরোয়ার্ড
        deposit_chat = db_query("SELECT chat_id FROM notify_chats WHERE chat_type='deposit'", fetchone=True)
        if deposit_chat:
            try: bot.send_message(deposit_chat[0], group_alert, reply_markup=group_markup, parse_mode="HTML")
            except Exception: pass
            
        bot.edit_message_text(f"{call.message.text}\n\n🟢 Approved Successfully!", call.message.chat.id, call.message.message_id)
    else:
        bot.send_message(target_id, "❌ <b>দুঃখিত! আপনার সাবমিট করা ডিপোজিট রিকোয়েস্টটি এডমিন প্যানেল দ্বারা রিজেক্ট করা হয়েছে।</b>", parse_mode="HTML")
        bot.edit_message_text(f"{call.message.text}\n\n🔴 Request Rejected!", call.message.chat.id, call.message.message_id)

# 🎁 REFER, ACCOUNT, ORDERS, SUPPORT, DEVELOPER HANDLERS 
@bot.message_handler(func=lambda m: m.text and ("REFER" in m.text))
def refer_handler(message):
    user_id = message.from_user.id
    user_data = db_query("SELECT verified_ref_count, total_ref_earnings FROM users WHERE user_id=?", (user_id,), fetchone=True)
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    msg = f"╭─────────────────────╮\n" \
          f"   🎁 <b>REFER AND EARN SYSTEM</b>\n" \
          f"╰─────────────────────╯\n" \
          f"আপনার বন্ধুদের বটের রেফারাল লিংক শেয়ার করে আকর্ষণীয় বোনাস ইনকাম করুন।\n\n" \
          f"🔗 <b>আপনার পার্সোনাল রেফারাল লিংক:</b>\n<code>{ref_link}</code>\n\n" \
          f"👥 <b>মোট সফল রেফারাল:</b> {user_data[0]} জন\n" \
          f"🪙 <b>সর্বমোট রেফারাল আর্নিং:</b> {user_data[1]:.2f} USDT"
    bot.send_message(user_id, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and ("MY ACCOUNT" in m.text))
def my_account(message):
    data = db_query("SELECT balance, total_deposit, total_product, joined_date FROM users WHERE user_id=?", (message.from_user.id,), fetchone=True)
    rate = float(db_query("SELECT value FROM settings WHERE key='usdt_rate'", fetchone=True)[0])
    if data:
        calc_bdt_bal = data[0] * rate
        msg = f"╭─────────────────────╮\n" \
              f"   👤 <b>YOUR ACCOUNT STATS</b>\n" \
              f"╰─────────────────────╯\n" \
              f"🪙 <b>Wallet Balance:</b> {data[0]:.2f} USDT (~৳{calc_bdt_bal:.2f} BDT)\n" \
              f"📥 <b>Total Deposit:</b> {data[1]:.2f} USDT\n" \
              f"📦 <b>Purchased Products:</b> {data[2]} Pcs\n" \
              f"📅 <b>Registration Date:</b> {data[3]}\n" \
              f"──────────────────────"
        bot.send_message(message.chat.id, msg, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and ("MY ORDERS" in m.text))
def my_orders_handler(message):
    purchases = db_query("SELECT product_name, purchase_date FROM purchases WHERE user_id=? ORDER BY id DESC", (message.from_user.id,), fetchall=True)
    if not purchases:
        bot.send_message(message.from_user.id, "📦 <b>আপনার অ্যাকাউন্টে কোনো অর্ডারের হিস্টোরি রেকর্ড পাওয়া যায়নি।</b>", parse_mode="HTML")
        return
    res = "╭─────────────────────╮\n   📦 <b>YOUR ORDER RECORD HISTORY</b>\n╰─────────────────────╯\n"
    for idx, item in enumerate(purchases, start=1):
        res += f"<b>{idx}.</b> {item[0]} \n📅 <i>Date: {item[1]}</i>\n"
    bot.send_message(message.from_user.id, res, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and ("SUPPORT" in m.text))
def support_info(message):
    link = db_query("SELECT value FROM settings WHERE key='support_link'", fetchone=True)[0]
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🚀 Contact Customer Support", url=link))
    bot.send_message(message.chat.id, "💬 <b>যেকোনো সমস্যা বা তথ্যের জন্য সরাসরি আমাদের কাস্টমার সাপোর্ট এজেন্টের সাথে যোগাযোগ করুন:</b>", reply_markup=markup, parse_mode="HTML")

@bot.message_handler(func=lambda m: m.text and ("DEVELOPER" in m.text))
def developer_info(message):
    dev_url = db_query("SELECT value FROM settings WHERE key='dev_link'", fetchone=True)[0]
    markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🖥 Contact Official Developer", url=dev_url))
    bot.send_message(message.chat.id, "👨‍💻 <b>বটের কোনো টেকনিক্যাল বাগ বা মডিফিকেশনের জন্য সরাসরি ডেভেলপারের সাথে যোগাযোগ করতে পারেন:</b>", reply_markup=markup, parse_mode="HTML")


# 👑 ৭. ওনার ও মাল্টি-লেভেল এডমিন কন্ট্রোল প্যানেল
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    uid = message.from_user.id
    if not is_any_admin(uid): return
    
    markup = types.InlineKeyboardMarkup()
    
    if uid == OWNER_ID:
        markup.row(types.InlineKeyboardButton("📁 ক্যাটাগরি তৈরি", callback_data="adm_make_cat"), types.InlineKeyboardButton("🔑", callback_data="perm_products"))
        markup.row(types.InlineKeyboardButton("➕ প্রোডাক্ট যুক্ত করুন", callback_data="adm_add_prod_btn"), types.InlineKeyboardButton("🔑", callback_data="perm_add_prod"))
        markup.row(types.InlineKeyboardButton("❌ প্রোডাক্ট রিমুভ", callback_data="adm_rem_prod"), types.InlineKeyboardButton("🔑", callback_data="perm_rem_prod"))
        markup.row(types.InlineKeyboardButton("⚙️ পেমেন্ট নম্বর পরিবর্তন", callback_data="adm_payment_address"), types.InlineKeyboardButton("🔑", callback_data="perm_gateways"))
        markup.row(types.InlineKeyboardButton("🎛 গেটওয়ে অন/অফ সুইচ", callback_data="adm_toggle_gate"), types.InlineKeyboardButton("🔑", callback_data="perm_toggle_gate"))
        markup.row(types.InlineKeyboardButton("🔗 বটের লিংক কন্ট্রোল", callback_data="adm_bot_links"), types.InlineKeyboardButton("🔑", callback_data="perm_bot_links"))
        markup.row(types.InlineKeyboardButton("📊 USDT রেট আপডেট", callback_data="adm_update_usdt_rate"), types.InlineKeyboardButton("🔑", callback_data="perm_gateways"))
        markup.row(types.InlineKeyboardButton("🎨 বোতামের ইমোজি চেঞ্জ", callback_data="adm_change_emojis"), types.InlineKeyboardButton("🔑", callback_data="perm_emojis"))
        markup.row(types.InlineKeyboardButton("📢 বাটনসহ ডাইনামিক পোস্ট", callback_data="adm_create_custom_post"), types.InlineKeyboardButton("🔑", callback_data="perm_custom_post"))
        
        # ৩টি আলাদা নোটিফিকেশন চ্যানেল কন্ট্রোল বাটন
        markup.row(types.InlineKeyboardButton("🔔 নোটিফিকেশন চ্যানেল সেটআপ", callback_data="adm_setup_notify"), types.InlineKeyboardButton("🔑", callback_data="perm_notify_chat"))
        
        markup.row(types.InlineKeyboardButton("👤 ইউজার এড / ম্যানেজ", callback_data="adm_add_user"), types.InlineKeyboardButton("🔑", callback_data="perm_manage_user"))
        markup.row(types.InlineKeyboardButton("❌ ইউজার সম্পূর্ণ ডিলিট", callback_data="adm_delete_user"), types.InlineKeyboardButton("🔑", callback_data="perm_manage_user"))
        markup.row(types.InlineKeyboardButton("📢 ফোর্স জয়েন চ্যানেল যুক্ত", callback_data="adm_add_chan"), types.InlineKeyboardButton("🔑", callback_data="perm_force_join"))
        markup.row(types.InlineKeyboardButton("👥 গ্লোবাল ব্রডকাস্ট নোটিশ", callback_data="adm_broadcast"), types.InlineKeyboardButton("🔑", callback_data="perm_broadcast"))
        
        bot.send_message(OWNER_ID, "👑 <b>OWNER SUPREME CONTROL PANEL</b>\n\nফিচার ইউজ করুন অথবা এডমিন এড করতে ফিচারের পাশের 🔑 বাটনে ক্লিক করুন:", reply_markup=markup, parse_mode="HTML")
    else:
        if has_permission(uid, "products"): markup.add(types.InlineKeyboardButton("📁 ক্যাটাগরি তৈরি", callback_data="adm_make_cat"))
        if has_permission(uid, "add_prod"): markup.add(types.InlineKeyboardButton("➕ প্রোডাক্ট যুক্ত করুন", callback_data="adm_add_prod_btn"))
        if has_permission(uid, "rem_prod"): markup.add(types.InlineKeyboardButton("❌ প্রোডাক্ট রিমুভ", callback_data="adm_rem_prod"))
        if has_permission(uid, "gateways"): 
            markup.add(types.InlineKeyboardButton("⚙️ পেমেন্ট নম্বর পরিবর্তন", callback_data="adm_payment_address"))
            markup.add(types.InlineKeyboardButton("📊 USDT রেট আপডেট", callback_data="adm_update_usdt_rate"))
        if has_permission(uid, "toggle_gate"): markup.add(types.InlineKeyboardButton("🎛 গেটওয়ে অন/অফ সুইচ", callback_data="adm_toggle_gate"))
        if has_permission(uid, "bot_links"): markup.add(types.InlineKeyboardButton("🔗 বটের লিংক কন্ট্রোল", callback_data="adm_bot_links"))
        if has_permission(uid, "emojis"): markup.add(types.InlineKeyboardButton("🎨 বোতামের ইমোজি চেঞ্জ", callback_data="adm_change_emojis"))
        if has_permission(uid, "custom_post"): markup.add(types.InlineKeyboardButton("📢 বাটনসহ ডাইনামিক পোস্ট", callback_data="adm_create_custom_post"))
        if has_permission(uid, "notify_chat"): markup.add(types.InlineKeyboardButton("🔔 নোটিফিকেশন চ্যানেল সেটআপ", callback_data="adm_setup_notify"))
        if has_permission(uid, "manage_user"): 
            markup.add(types.InlineKeyboardButton("👤 ইউজার এড / ম্যানেজ", callback_data="adm_add_user"))
            markup.add(types.InlineKeyboardButton("❌ ইউজার সম্পূর্ণ ডিলিট", callback_data="adm_delete_user"))
        if has_permission(uid, "force_join"): markup.add(types.InlineKeyboardButton("📢 ফোর্স জয়েন চ্যানেল যুক্ত", callback_data="adm_add_chan"))
        if has_permission(uid, "broadcast"): markup.add(types.InlineKeyboardButton("👥 গ্লোবাল ব্রডকাস্ট নোটিশ", callback_data="adm_broadcast"))
        
        bot.send_message(uid, "🎛 <b>ADMIN SUB PANEL</b>\n\nআপনার জন্য অনুমোদিত ফিচারসমূহ নিচে দেওয়া হলো:", reply_markup=markup, parse_mode="HTML")

# 🔄 এডমিন ও ওনার অ্যাকশন হ্যান্ডলারস
@bot.callback_query_handler(func=lambda call: call.data.startswith(('adm_', 'perm_')))
def admin_actions(call):
    uid = call.from_user.id
    action = call.data
    
    if action.startswith('perm_'):
        if uid != OWNER_ID: return
        perm_name = action.replace('perm_', '')
        msg = bot.send_message(OWNER_ID, f"🔑 যে এডমিনকে <code>{perm_name}</code> সেকশনের দায়িত্ব দিতে চান তার Telegram Chat ID দিন:")
        bot.register_next_step_handler(msg, save_admin_permission, perm_name)
        return

    if action == "adm_make_cat":
        if not has_permission(uid, "products"): return
        msg = bot.send_message(uid, "📁 নতুন ক্যাটাগরির নাম লিখুন:")
        bot.register_next_step_handler(msg, save_category)
    elif action == "adm_add_prod_btn":
        if not has_permission(uid, "add_prod"): return
        categories = db_query("SELECT id, name FROM categories", fetchall=True)
        if not categories:
            bot.send_message(uid, "❌ আগে ক্যাটাগরি তৈরি করুন!")
            return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for cat in categories:
            markup.add(types.InlineKeyboardButton(f"📁 {cat[1]}", callback_data=f"selcat_{cat[0]}"))
        bot.send_message(uid, "👉 প্রোডাক্ট ক্যাটাগরি বাটনটি সিলেক্ট করুন:", reply_markup=markup)
    elif action == "adm_rem_prod":
        if not has_permission(uid, "rem_prod"): return
        prods = db_query("SELECT id, name FROM products", fetchall=True)
        text = "\n".join([f"ID: {p[0]} - {p[1]}" for p in prods])
        msg = bot.send_message(uid, f"{text}\n\nযে প্রোডাক্টটি ডিলিট করতে চান তার ID লিখুন:")
        bot.register_next_step_handler(msg, delete_product)
    elif action == "adm_payment_address":
        if not has_permission(uid, "gateways"): return
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("📱 বিকাশ নম্বর পরিবর্তন", callback_data="edit_num_bkash_num"),
            types.InlineKeyboardButton("📱 নগদ নম্বর পরিবর্তন", callback_data="edit_num_nagad_num"),
            types.InlineKeyboardButton("📱 রকেট নম্বর পরিবর্তন", callback_data="edit_num_rocket_num"),
            types.InlineKeyboardButton("🔶 Binance Pay ID পরিবর্তন", callback_data="edit_num_binance_pay")
        )
        bot.send_message(uid, "💳 <b>পেমেন্ট নম্বর পরিবর্তন সেকশন:</b>", reply_markup=markup, parse_mode="HTML")
    elif action == "adm_toggle_gate":
        if not has_permission(uid, "toggle_gate"): return
        markup = types.InlineKeyboardMarkup(row_width=1)
        for g in ['bkash', 'nagad', 'rocket', 'binance']:
            curr = db_query(f"SELECT value FROM settings WHERE key='status_{g}'", fetchone=True)[0]
            markup.add(types.InlineKeyboardButton(f"{g.upper()} - Current: {curr}", callback_data=f"toggle_{g}"))
        bot.send_message(uid, "🎛 <b>পেমেন্ট গেটওয়ে অন/অফ সুইচ প্যানেল:</b>", reply_markup=markup, parse_mode="HTML")
    elif action == "adm_bot_links":
        if not has_permission(uid, "bot_links"): return
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🛍 SHOP Link পরিবর্তন", callback_data="edit_link_shop_link"),
            types.InlineKeyboardButton("💬 Support Link পরিবর্তন", callback_data="edit_link_support_link"),
            types.InlineKeyboardButton("👨‍💻 Developer Link পরিবর্তন", callback_data="edit_link_dev_link")
        )
        bot.send_message(uid, "🔗 <b>বটের সকল লিংক কন্ট্রোল প্যানেল:</b>", reply_markup=markup, parse_mode="HTML")
    elif action == "adm_update_usdt_rate":
        if not has_permission(uid, "gateways"): return
        curr_rate = db_query("SELECT value FROM settings WHERE key='usdt_rate'", fetchone=True)[0]
        msg = bot.send_message(uid, f"📊 বর্তমান রেট: ১ USDT = {curr_rate} BDT\n\nনতুন রেট কত সেট করতে চান তা সংখ্যায় দিন:")
        bot.register_next_step_handler(msg, save_usdt_rate)
    elif action == "adm_change_emojis":
        if not has_permission(uid, "emojis"): return
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🛍 BUY SHOP PRODUCT ইমোজি", callback_data="edit_emo_emo_buy"),
            types.InlineKeyboardButton("💳 DEPOSIT MONEY ইমোজি", callback_data="edit_emo_emo_dep"),
            types.InlineKeyboardButton("🎁 REFER ইমোজি", callback_data="edit_emo_emo_ref"),
            types.InlineKeyboardButton("📦 MY ORDERS ইমোজি", callback_data="edit_emo_emo_ord"),
            types.InlineKeyboardButton("👤 MY ACCOUNT ইমোজি", callback_data="edit_emo_emo_acc"),
            types.InlineKeyboardButton("💬 SUPPORT ইমোজি", callback_data="edit_emo_emo_sup"),
            types.InlineKeyboardButton("👨‍💻 DEVELOPER ইমোজি", callback_data="edit_emo_emo_dev")
        )
        bot.send_message(uid, "🎨 <b>বাটন ইমোজি চেঞ্জ প্যানেল:</b>", reply_markup=markup)
    elif action == "adm_create_custom_post":
        if not has_permission(uid, "custom_post"): return
        msg = bot.send_message(uid, "🆔 টার্গেট চ্যাট আইডি দিন (যেমন: -100xxxxxxxxxx):")
        bot.register_next_step_handler(msg, step_post_text)
        
    # ৩টি আলাদা চ্যানেলের নতুন সাব-মেনু কনফিগারেশন
    elif action == "adm_setup_notify":
        if not has_permission(uid, "notify_chat"): return
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("💳 Deposit Channel সেটআপ", callback_data="setnotify_deposit"),
            types.InlineKeyboardButton("🛍 Purchase Channel সেটআপ", callback_data="setnotify_purchase"),
            types.InlineKeyboardButton("👋 User Join Channel সেটআপ", callback_data="setnotify_user_join")
        )
        bot.edit_message_text("🔔 <b>নোটিফিকেশন চ্যানেল কনফিগারেশন প্যানেল:</b>\n\nযে কোনো একটি অপশন সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup, parse_mode="HTML")
        
    elif action == "adm_add_user":
        if not has_permission(uid, "manage_user"): return
        msg = bot.send_message(uid, "👤 নতুন ইউজারের Telegram Chat ID দিন:")
        bot.register_next_step_handler(msg, process_add_user_manually)
    elif action == "adm_delete_user":
        if not has_permission(uid, "manage_user"): return
        msg = bot.send_message(uid, "❌ যে ইউজারকে ডিলিট করতে চান তার Telegram ID দিন:")
        bot.register_next_step_handler(msg, process_delete_user_completely)
    elif action == "adm_add_chan":
        if not has_permission(uid, "force_join"): return
        msg = bot.send_message(uid, "📢 ফোর্স জয়েন সেট করতে গ্রুপ বা চ্যানেলের চ্যাট আইডি দিন (যেমন: -100xxxxxxxxxx):")
        bot.register_next_step_handler(msg, save_channel)
    elif action == "adm_broadcast":
        if not has_permission(uid, "broadcast"): return
        msg = bot.send_message(uid, "📢 গ্লোবাল ব্রডকাস্ট নোটিশ মেসেজটি লিখুন:")
        bot.register_next_step_handler(msg, run_broadcast)

# 🔑 পারমিশন সেভ লজিক
def save_admin_permission(message, perm_name):
    target_id = message.text.strip()
    if target_id.isdigit():
        db_query("INSERT OR REPLACE INTO admin_permissions (user_id, permission) VALUES (?, ?)", (int(target_id), perm_name), commit=True)
        bot.send_message(OWNER_ID, f"✅ সফলভাবে ইউজার {target_id} কে <b>{perm_name}</b> সেকশনের কন্ট্রোল অ্যাক্সেস দেওয়া হয়েছে।", parse_mode="HTML")
    else: bot.send_message(OWNER_ID, "❌ ভুল আইডি!")

# 📊 USDT রেট আপডেটার লজিক
def save_usdt_rate(message):
    new_rate = message.text.strip()
    if new_rate.isdigit():
        db_query("UPDATE settings SET value=? WHERE key='usdt_rate'", (new_rate,), commit=True)
        bot.send_message(message.chat.id, f"✅ <b>USDT বিনিময় হার সফলভাবে আপডেট হয়েছে! বর্তমান রেট: 1 USDT = {new_rate} BDT</b>", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ শুধুমাত্র সংখ্যা দিন।")

# 📢 ৩টি আলাদা নোটিফিকেশন চ্যানেল সেভ করার লজিক
@bot.callback_query_handler(func=lambda call: call.data.startswith('setnotify_'))
def handle_set_notify_channel(call):
    chat_type = call.data.split('_')[1] if 'user_join' not in call.data else 'user_join'
    msg = bot.send_message(call.from_user.id, f"🎯 <b>{chat_type.upper()}</b> অ্যালার্ট ফরোয়ার্ডের জন্য গ্রুপ/চ্যানেলের Chat ID দিন (যেমন: -100xxxxxxxxxx):", parse_mode="HTML")
    bot.register_next_step_handler(msg, save_notify_chat, chat_type)

def save_notify_chat(message, chat_type):
    c_id = message.text.strip()
    try:
        chat_info = bot.get_chat(c_id)
        c_name = chat_info.title if chat_info.title else "Group/Channel"
        db_query("INSERT OR REPLACE INTO notify_chats (chat_type, chat_id, chat_name) VALUES (?, ?, ?)", (chat_type, c_id, c_name), commit=True)
        bot.send_message(message.chat.id, f"✅ <b>{chat_type.upper()} নোটিফিকেশন চ্যানেল সেট হয়েছে!</b>\n📌 নাম: {c_name}\n🆔 আইডি: {c_id}", parse_mode="HTML")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ কানেক্ট করা যায়নি। বটকে ওই চ্যাটে এডমিন দিয়ে ID সাবমিট করুন।\nError: {e}")

# 📢 ডাইনামিক পোস্ট প্রসেস
def step_post_text(message):
    chat_target = message.text.strip()
    msg = bot.send_message(message.chat.id, "✍️ এবার নোটিশ টেক্সটটি লিখুন:")
    bot.register_next_step_handler(msg, step_button_title, chat_target)

def step_button_title(message, chat_target):
    post_desc = message.text
    msg = bot.send_message(message.chat.id, "🔘 বাটনের নাম/টাইটেল লিখুন:")
    bot.register_next_step_handler(msg, step_button_url, chat_target, post_desc)

def step_button_url(message, chat_target, post_desc):
    btn_title = message.text.strip()
    msg = bot.send_message(message.chat.id, f"🔗 বাটনে যে লিংকটি অ্যাড করতে চান তা দিন:")
    bot.register_next_step_handler(msg, finalize_dynamic_post, chat_target, post_desc, btn_title)

def finalize_dynamic_post(message, chat_target, post_desc, btn_title):
    btn_link = message.text.strip()
    if not btn_link.startswith("http"):
        bot.send_message(message.chat.id, "❌ ভুল লিংক ফরম্যাট!")
        return
    custom_markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text=btn_title, url=btn_link))
    try:
        bot.send_message(chat_id=chat_target, text=post_desc, reply_markup=custom_markup, parse_mode="HTML")
        bot.send_message(message.chat.id, f"✅ সফলভাবে পোস্ট করা হয়েছে!")
    except Exception as e: bot.send_message(message.chat.id, f"❌ ব্যর্থ। Error: {e}")

# 🎨 ইমোজি এডিট
@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_emo_'))
def prompt_emoji_edit(call):
    key = call.data.replace('edit_emo_', '')
    msg = bot.send_message(call.from_user.id, "✍️ নতুন ইমোজি ইনপুট দিন:")
    bot.register_next_step_handler(msg, save_new_emoji, key)

def save_new_emoji(message, key):
    new_emoji = message.text.strip()
    db_query("UPDATE settings SET value=? WHERE key=?", (new_emoji, key), commit=True)
    bot.send_message(message.chat.id, "✅ বাটন ইমোজি পরিবর্তন সফল।")

# 🔗 লিংক এডিট
@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_link_'))
def prompt_link_edit(call):
    key = call.data.replace('edit_link_', '')
    msg = bot.send_message(call.from_user.id, f"✍️ নতুন URL/লিংকটি দিন:")
    bot.register_next_step_handler(msg, save_bot_dynamic_link, key)

def save_bot_dynamic_link(message, key):
    new_url = message.text.strip()
    db_query("UPDATE settings SET value=? WHERE key=?", (new_url, key), commit=True)
    bot.send_message(message.chat.id, f"✅ সফলভাবে লিংক আপডেট করা হয়েছে।")

# 👤 ইউজার ম্যানেজমেন্ট
def process_add_user_manually(message):
    uid = message.text.strip()
    if not uid.isdigit(): return
    exists = db_query("SELECT user_id FROM users WHERE user_id=?", (int(uid),), fetchone=True)
    if exists: bot.send_message(message.chat.id, "⚠️ ইউজার ইতিমধ্যে আছে।")
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")
        db_query("INSERT INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)", (int(uid), "@Added_Manually", "Manual User", date_str), commit=True)
        bot.send_message(message.chat.id, f"✅ ইউজার {uid} অ্যাড করা হয়েছে।")

def process_delete_user_completely(message):
    uid = message.text.strip()
    if not uid.isdigit(): return
    target_id = int(uid)
    db_query("DELETE FROM users WHERE user_id=?", (target_id,), commit=True)
    db_query("DELETE FROM purchases WHERE user_id=?", (target_id,), commit=True)
    db_query("DELETE FROM settings WHERE key=?", (f"tx_{target_id}",), commit=True)
    bot.send_message(message.chat.id, f"🗑 ইউজার রেকর্ড সম্পূর্ণ ডিলিট সম্পন্ন।")

# 🆕 প্রোডাক্ট আপলোড
@bot.callback_query_handler(func=lambda call: call.data.startswith('selcat_'))
def handle_category_button_click(call):
    cat_id = call.data.split('_')[1]
    bot.delete_message(call.message.chat.id, call.message.message_id)
    msg = bot.send_message(call.from_user.id, "📝 প্রোডাক্টের নাম লিখুন:")
    bot.register_next_step_handler(msg, step_prod_price, cat_id)

def step_prod_price(message, cat_id):
    prod_name = message.text.strip()
    msg = bot.send_message(message.chat.id, f"💰 {prod_name} এর প্রাইস BDT-তে লিখুন:")
    bot.register_next_step_handler(msg, step_prod_link, cat_id, prod_name)

def step_prod_link(message, cat_id, prod_name):
    try: price_bdt = float(message.text.strip())
    except ValueError: return
    msg = bot.send_message(message.chat.id, f"👀 ফটো লিংক (URL) দিন:")
    bot.register_next_step_handler(msg, step_prod_file, cat_id, prod_name, price_bdt)

def step_prod_file(message, cat_id, prod_name, price_bdt):
    photo_url = message.text.strip()
    msg = bot.send_message(message.chat.id, "📁 প্রোডাক্টের মূল প্রিমিয়াম ফাইল বা ডকুমেন্টটি এখানে আপলোড করুন:")
    bot.register_next_step_handler(msg, step_prod_finalize, cat_id, prod_name, price_bdt, photo_url)

def step_prod_finalize(message, cat_id, prod_name, price_bdt, photo_url):
    if message.content_type != 'document': return
    file_id = message.document.file_id
    db_query("INSERT INTO products (category_id, name, price_bdt, price_usdt, file_id, photo_url) VALUES (?, ?, ?, 0.0, ?, ?)",
             (int(cat_id), prod_name, price_bdt, file_id, photo_url), commit=True)
    bot.send_message(message.chat.id, f"✅ প্রোডাক্ট সাকসেসফুলি লাইভ হয়েছে।")

# 💳 পেমেন্ট এডিট ও গেটওয়ে সুইচ
@bot.callback_query_handler(func=lambda call: call.data.startswith('edit_num_'))
def prompt_edit_payment_address(call):
    key = call.data.replace('edit_num_', '')
    msg = bot.send_message(call.from_user.id, f"✍️ নতুন নম্বর/অ্যাড্রেসটি ইনপুট দিন:")
    bot.register_next_step_handler(msg, save_payment_address, key)

def save_payment_address(message, key):
    new_val = message.text.strip()
    db_query("UPDATE settings SET value=? WHERE key=?", (new_val, key), commit=True)
    bot.send_message(message.chat.id, "✅ পেমেন্ট নম্বর আপডেট সফল।")

@bot.callback_query_handler(func=lambda call: call.data.startswith('toggle_'))
def toggle_gateway_status(call):
    if not has_permission(call.from_user.id, "toggle_gate"): return
    gateway = call.data.split('_')[1]
    key = f"status_{gateway}"
    current = db_query("SELECT value FROM settings WHERE key=?", (key,), fetchone=True)[0]
    new_status = "OFF" if current == "ON" else "ON"
    db_query("UPDATE settings SET value=? WHERE key=?", (new_status, key), commit=True)
    bot.answer_callback_query(call.id, f"✅ {gateway.upper()} {new_status} করা হয়েছে!", show_alert=True)
    bot.delete_message(call.message.chat.id, call.message.message_id)

def save_category(message):
    db_query("INSERT INTO categories (name) VALUES (?)", (message.text.strip(),), commit=True)
    bot.send_message(message.chat.id, "✅ ক্যাটাগরি তৈরি সফল!")

def delete_product(message):
    db_query("DELETE FROM products WHERE id=?", (int(message.text.strip()),), commit=True)
    bot.send_message(message.chat.id, "✅ প্রোডাক্ট রিমুভ করা হয়েছে।")

def save_channel(message):
    ch_id = message.text.strip()
    try:
        chat_info = bot.get_chat(ch_id)
        ch_type = chat_info.type
        ch_link = chat_info.invite_link if chat_info.invite_link else bot.export_chat_invite_link(ch_id)
        db_query("INSERT OR REPLACE INTO force_channels (channel_id, invite_link, type) VALUES (?, ?, ?)", (ch_id, ch_link, ch_type), commit=True)
        bot.send_message(message.chat.id, f"✅ নতুন ফোর্স জয়েন চ্যানেল সফলভাবে যুক্ত হয়েছে!")
    except Exception as e: bot.send_message(message.chat.id, f"❌ ব্যর্থ! Error: {e}")

def run_broadcast(message):
    users = db_query("SELECT user_id FROM users", fetchall=True)
    count = 0
    for u in users:
        try:
            bot.send_message(u[0], f"📢 <b>গুরুত্বপূর্ণ গ্লোবাল নোটিশ:</b>\n\n{message.text}", parse_mode="HTML")
            count += 1
        except Exception: continue
    bot.send_message(message.chat.id, f"✅ সফলভাবে {count} জনের কাছে নোটিশ পাঠানো হয়েছে।")

# ↩️ কমন নেভিগেশন
@bot.callback_query_handler(func=lambda call: call.data in ['go_home', 'back_to_shop'])
def navigate(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    if call.data == 'go_home':
        bot.send_message(call.message.chat.id, "🏠 <b>মূল মেনু:</b>", reply_markup=main_keyboard(), parse_mode="HTML")
    elif call.data == 'back_to_shop': buy_shop_product(call.message)

# 🎛 মেনু সেটআপ
try:
    bot.set_my_commands([types.BotCommand("start", "🚀 Start Bot"), types.BotCommand("admin", "📌 Open Admin Panel")], scope=types.BotCommandScopeChat(chat_id=OWNER_ID))
    bot.set_my_commands([types.BotCommand("start", "🚀 Start Bot")], scope=types.BotCommandScopeAllPrivateChats())
except Exception: pass

print("⚡ Ultra Premium Design Bot Running smoothly...")
bot.infinity_polling()
