import os
import sqlite3
import time
import telebot
from telebot import types

TOKEN = "8945119230:AAFGgBCxgadcIQFWyDqS1MYr0KOZS_HMW8U"
ADMIN_IDS = [6186783925, 8849219521]

bot = telebot.TeleBot(TOKEN)

# Admin panelinden dosya ekleme haritası
CATEGORY_DOSYA_MAP = {
    "add_turkcell": "turkcell.hc",
    "add_vodafone": "vodafone.hc",
    "add_turktelekom": "turktelekom.hc",
    "add_vip_turkcell": "vip_turkcell.hc",
    "add_vip_vodafone": "vip_vodafone.hc",
    "add_vip_turktelekom": "vip_turktelekom.hc",
    "add_serit_kapak": "serit_kapak.hc",
    "add_serit": "serit.hc",

    # TLS Servisleri
    "add_tls_chatgpt": "tls_chatgpt.hc",
    "add_tls_whatsapp": "tls_whatsapp.hc",
    "add_tls_speedtest": "tls_speedtest.hc",
    "add_tls_telegram": "tls_telegram.hc",
    "add_tls_youtube": "tls_youtube.hc",
    "add_tls_tiktok": "tls_tiktok.hc",
    "add_tls_facebook": "tls_facebook.hc",

    # HTTP Custom Servisleri
    "add_http_chatgpt": "http_chatgpt.hc",
    "add_http_whatsapp": "http_whatsapp.hc",
    "add_http_speedtest": "http_speedtest.hc",
    "add_http_telegram": "http_telegram.hc",
    "add_http_youtube": "http_youtube.hc",
    "add_http_tiktok": "http_tiktok.hc",
    "add_http_facebook": "http_facebook.hc",

    # V2Ray Servisleri
    "add_v2ray_chatgpt": "v2ray_chatgpt.hc",
    "add_v2ray_whatsapp": "v2ray_whatsapp.hc",
    "add_v2ray_speedtest": "v2ray_speedtest.hc",
    "add_v2ray_telegram": "v2ray_telegram.hc",
    "add_v2ray_youtube": "v2ray_youtube.hc",
    "add_v2ray_tiktok": "v2ray_tiktok.hc",
    "add_v2ray_facebook": "v2ray_facebook.hc",

    # NPVT Servisleri
    "add_npvt_chatgpt": "npvt_chatgpt.hc",
    "add_npvt_whatsapp": "npvt_whatsapp.hc",
    "add_npvt_speedtest": "npvt_speedtest.hc",
    "add_npvt_telegram": "npvt_telegram.hc",
    "add_npvt_youtube": "npvt_youtube.hc",
    "add_npvt_tiktok": "npvt_tiktok.hc",
    "add_npvt_facebook": "npvt_facebook.hc",
}

admin_secimleri = {}
gecici_secim = {}
admin_puan_bekleyenler = set()
admin_ban_bekleyenler = set()
admin_unban_bekleyenler = set()

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points INTEGER DEFAULT 50,
            last_bonus INTEGER DEFAULT 0,
            referred_by INTEGER DEFAULT 0,
            is_banned INTEGER DEFAULT 0
        )
    """)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_bonus INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

init_db()

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_user_banned(user_id):
    if is_admin(user_id):
        return False
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT is_banned FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row and row[0] == 1

def get_user(user_id, username="", referrer_id=None):
    if is_admin(user_id):
        return 999999999
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT points, last_bonus, referred_by FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        ref_id = referrer_id if referrer_id and referrer_id != user_id else 0
        cursor.execute("INSERT INTO users (user_id, username, points, last_bonus, referred_by, is_banned) VALUES (?, ?, ?, ?, ?, 0)", (user_id, username, 50, 0, ref_id))
        conn.commit()
        
        if ref_id != 0 and not is_admin(ref_id):
            cursor.execute("UPDATE users SET points = points + 15 WHERE user_id = ?", (ref_id,))
            conn.commit()
            try:
                bot.send_message(ref_id, "🎉 Tebrikler! Davet ettiğin bir kullanıcı botu başlattığı için hesabına **15 Puan** eklendi.")
            except Exception:
                pass

        points = 50
    else:
        points = row[0]
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()
    conn.close()
    return points

def update_points(user_id, amount):
    if is_admin(user_id):
        return
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def set_ban_status(user_id, status):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (status, user_id))
    conn.commit()
    conn.close()

def check_and_update_bonus(user_id):
    if is_admin(user_id):
        return True, 0
    current_time = int(time.time())
    cooldown = 86400
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT last_bonus FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        last_bonus = row[0] or 0
        time_passed = current_time - last_bonus
        if time_passed < cooldown:
            remaining_time = cooldown - time_passed
            hours = remaining_time // 3600
            minutes = (remaining_time % 3600) // 60
            conn.close()
            return False, f"{hours} saat {minutes} dakika"
    cursor.execute("UPDATE users SET last_bonus = ? WHERE user_id = ?", (current_time, user_id))
    conn.commit()
    conn.close()
    return True, 0

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if is_user_banned(user_id):
        bot.send_message(message.chat.id, "❌ Bot tarafında yasaklandınız (Banlısınız). İşlem yapamazsınız.")
        return

    username = message.from_user.username or "Bilinmiyor"
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].isdigit():
        potential_ref = int(args[1])
        if potential_ref != user_id:
            referrer_id = potential_ref

    get_user(user_id, username, referrer_id)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(types.KeyboardButton("🛍️ Market"))
    markup.add(types.KeyboardButton("🔐 VPN Menüsü"))
    markup.add(types.KeyboardButton("🪙 Puanım & Görevler"))
    markup.add(types.KeyboardButton("👥 Davet Et Kazan"))
    markup.add(types.KeyboardButton("💰 Bakiye"))
    markup.add(types.KeyboardButton("🎧 Destek"))
    
    if is_admin(user_id):
        markup.add(types.KeyboardButton("🛠️ Admin Paneli"))

    bot.send_message(message.chat.id, "👋 Hoş geldin! Aşağıdaki menüyü kullanarak işlemlerini yapabilirsin.", reply_markup=markup)

@bot.message_handler(content_types=['document'], func=lambda message: is_admin(message.from_user.id))
def handle_docs(message):
    user_id = message.from_user.id
    if user_id not in admin_secimleri or not admin_secimleri[user_id]:
        bot.reply_to(message, "⚠️ Önce Admin Paneli > Dosya Ekle kısmından paket seç!")
        return
    hedef_dosya = admin_secimleri[user_id]
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(hedef_dosya, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.reply_to(message, f"✅ Başarıyla `{hedef_dosya}` kaydedildi!", parse_mode="Markdown")
        admin_secimleri[user_id] = None
    except Exception as e:
        bot.reply_to(message, f"❌ Hata: {e}")

@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    text = message.text
    user_id = message.from_user.id

    if not is_admin(user_id) and is_user_banned(user_id):
        bot.send_message(message.chat.id, "❌ Yasaklı olduğunuz için işlem yapamazsınız.")
        return

    # Admin Puan Gönder Bekleme
    if is_admin(user_id) and user_id in admin_puan_bekleyenler:
        admin_puan_bekleyenler.remove(user_id)
        try:
            parts = text.split()
            target_id = int(parts[0])
            amount = int(parts[1])
            update_points(target_id, amount)
            bot.reply_to(message, f"✅ Başarılı! `{target_id}` ID'li kullanıcıya **{amount} Puan** eklendi.", parse_mode="Markdown")
        except Exception:
            bot.reply_to(message, "❌ Hatalı format! Örnek: `123456789 100`", parse_mode="Markdown")
        return

    # Admin Ban Atma Bekleme
    if is_admin(user_id) and user_id in admin_ban_bekleyenler:
        admin_ban_bekleyenler.remove(user_id)
        try:
            target_id = int(text.strip())
            if is_admin(target_id):
                bot.reply_to(message, "❌ Diğer adminleri banlayamazsın!")
                return
            set_ban_status(target_id, 1)
            bot.reply_to(message, f"✅ Başarılı! `{target_id}` ID'li kullanıcı banlandı.", parse_mode="Markdown")
        except Exception:
            bot.reply_to(message, "❌ Geçersiz ID! Sadece rakam giriniz.")
        return

    # Admin Ban Kaldırma Bekleme
    if is_admin(user_id) and user_id in admin_unban_bekleyenler:
        admin_unban_bekleyenler.remove(user_id)
        try:
            target_id = int(text.strip())
            set_ban_status(target_id, 0)
            bot.reply_to(message, f"✅ Başarılı! `{target_id}` ID'li kullanıcının banı kaldırıldı.", parse_mode="Markdown")
        except Exception:
            bot.reply_to(message, "❌ Geçersiz ID! Sadece rakam giriniz.")
        return

    if text == "🛍️ Market":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🎁 Şerit Kapak", callback_data="satinal_serit_kapak"))
        markup.add(types.InlineKeyboardButton("🎗️ Şerit", callback_data="satinal_serit"))
        markup.add(types.InlineKeyboardButton("💳 Vodafone Pay Kodları", callback_data="satinal_vodafone_pay"))
        markup.add(types.InlineKeyboardButton("🎮 Play Kodlar", callback_data="satinal_play_kod"))
        bot.send_message(message.chat.id, "🛍️ Market Kategorileri (Ürünler 200 Puandır):", reply_markup=markup)

    elif text == "🔐 VPN Menüsü":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🟢 Paketsiz VPN'ler", callback_data="menu_paketsiz"))
        markup.add(types.InlineKeyboardButton("📦 Paketli VPN'ler", callback_data="menu_paketli"))
        bot.send_message(message.chat.id, "🔐 VPN Ana Menüsü:", reply_markup=markup)

    elif text == "🪙 Puanım & Görevler":
        puan = get_user(user_id)
        puan_str = "Sınırsız ♾️" if is_admin(user_id) else str(puan)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🎁 Günlük Bonus Al (+20)", callback_data="task_bonus"))
        bot.send_message(message.chat.id, f"🪙 Mevcut Puanın: {puan_str}", reply_markup=markup)

    elif text == "👥 Davet Et Kazan":
        bot_info = bot.get_me()
        referral_link = f"https://t.me/{bot_info.username}?start={user_id}"
        bot.send_message(
            message.chat.id,
            f"👥 **Arkadaşını Davet Et, Puan Kazan!**\n\n"
            f"Her davet ettiğin kullanıcı başına **15 Puan** kazanırsın.\n\n"
            f"🔗 **Senin Davet Linkin:**\n`{referral_link}`\n\n"
            f"Bu linki arkadaşlarına göndererek puan kasabilirsin!",
            parse_mode="Markdown"
        )

    elif text == "💰 Bakiye":
        puan = get_user(user_id)
        puan_str = "Sınırsız ♾️" if is_admin(user_id) else f"{puan} Puan"
        bot.send_message(message.chat.id, f"💰 Güncel Bakiyen: {puan_str}")

    elif text == "🎧 Destek":
        bot.send_message(message.chat.id, "🎧 Destek Hattı: @Smsonay7")

    elif text == "🛠️ Admin Paneli" and is_admin(user_id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        markup.add(types.KeyboardButton("👥 Kullanıcıları Göster (İstatistik)"))
        markup.add(types.KeyboardButton("💸 Puan Gönder"))
        markup.add(types.KeyboardButton("🚫 Kullanıcı Banla"))
        markup.add(types.KeyboardButton("✅ Ban Kaldır"))
        markup.add(types.KeyboardButton("📂 Dosya Ekle"))
        markup.add(types.KeyboardButton("🔙 Ana Menüye Dön"))
        bot.send_message(message.chat.id, "🛠️ Admin Paneli:", reply_markup=markup)

    elif text == "🔙 Ana Menüye Dön" and is_admin(user_id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        markup.add(types.KeyboardButton("🛍️ Market"))
        markup.add(types.KeyboardButton("🔐 VPN Menüsü"))
        markup.add(types.KeyboardButton("🪙 Puanım & Görevler"))
        markup.add(types.KeyboardButton("👥 Davet Et Kazan"))
        markup.add(types.KeyboardButton("💰 Bakiye"))
        markup.add(types.KeyboardButton("🎧 Destek"))
        markup.add(types.KeyboardButton("🛠️ Admin Paneli"))
        bot.send_message(message.chat.id, "🔙 Ana menüye dönüldü.", reply_markup=markup)

    elif text == "👥 Kullanıcıları Göster (İstatistik)" and is_admin(user_id):
        conn = sqlite3.connect("bot_database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, points, is_banned FROM users")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            bot.send_message(message.chat.id, "📂 Henüz kayıtlı kullanıcı bulunmuyor.")
            return

        msg = f"📊 **Botu Kullanan Kullanıcılar ({len(rows)} Kişi):**\n\n"
        for row in rows:
            uid, uname, pts, banned = row
            durum = "🔴 Banlı" if banned == 1 else "🟢 Aktif"
            name_str = f"@{uname}" if uname and uname != "Bilinmiyor" else "İsimsiz"
            msg += f"• `{uid}` | {name_str} | **{pts} Puan** | {durum}\n"
            
            if len(msg) > 3500:
                bot.send_message(message.chat.id, msg, parse_mode="Markdown")
                msg = ""
        if msg:
            bot.send_message(message.chat.id, msg, parse_mode="Markdown")

    elif text == "💸 Puan Gönder" and is_admin(user_id):
        admin_puan_bekleyenler.add(user_id)
        bot.send_message(message.chat.id, "💸 Göndermek istediğin **Kullanıcı ID** ve **Puanı** yaz.\nÖrnek: `123456789 100`", parse_mode="Markdown")

    elif text == "🚫 Kullanıcı Banla" and is_admin(user_id):
        admin_ban_bekleyenler.add(user_id)
        bot.send_message(message.chat.id, "🚫 Banlamak istediğin **Kullanıcı ID**'sini yaz:", parse_mode="Markdown")

    elif text == "✅ Ban Kaldır" and is_admin(user_id):
        admin_unban_bekleyenler.add(user_id)
        bot.send_message(message.chat.id, "✅ Banını kaldırmak istediğin **Kullanıcı ID**'sini yaz:", parse_mode="Markdown")

    elif text == "📂 Dosya Ekle" and is_admin(user_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🟢 Paketsiz VPN Dosyaları Ekle", callback_data="admin_paketsiz"))
        markup.add(types.InlineKeyboardButton("📦 Paketli VPN Dosyaları Ekle", callback_data="admin_paketli_menu"))
        markup.add(types.InlineKeyboardButton("🎁 Şerit Kapak Dosyası Ekle", callback_data="add_serit_kapak"))
        markup.add(types.InlineKeyboardButton("🎗️ Şerit Dosyası Ekle", callback_data="add_serit"))
        bot.send_message(message.chat.id, "📂 Dosya Ekleme Ana Menüsü:", reply_markup=markup)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if not is_admin(user_id) and is_user_banned(user_id):
        bot.answer_callback_query(call.id, "❌ Yasaklısınız!", show_alert=True)
        return

    if call.data in CATEGORY_DOSYA_MAP:
        dosya_adi = CATEGORY_DOSYA_MAP[call.data]
        admin_secimleri[user_id] = dosya_adi
        bot.answer_callback_query(call.id, f"Seçildi: {dosya_adi}")
        bot.send_message(chat_id, f"✅ `{dosya_adi}` seçildi. Şimdi dosyayı belge olarak gönder.", parse_mode="Markdown")
        return

    if call.data == "admin_paketsiz":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🟡 Turkcell", callback_data="add_turkcell"))
        markup.add(types.InlineKeyboardButton("🔴 Vodafone", callback_data="add_vodafone"))
        markup.add(types.InlineKeyboardButton("🔵 Türk Telekom", callback_data="add_turktelekom"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="admin_geri_ana"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🟢 **Paketsiz Dosya Seç:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "admin_paketli_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔒 TLS Tünel", callback_data="admin_add_tls"))
        markup.add(types.InlineKeyboardButton("🌐 HTTP Custom", callback_data="admin_add_http"))
        markup.add(types.InlineKeyboardButton("🚀 V2Ray", callback_data="admin_add_v2ray"))
        markup.add(types.InlineKeyboardButton("⚡ NPVT", callback_data="admin_add_npvt"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="admin_geri_ana"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("📦 **Paketli Altyapı Seç:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "admin_geri_ana":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🟢 Paketsiz VPN Dosyaları Ekle", callback_data="admin_paketsiz"))
        markup.add(types.InlineKeyboardButton("📦 Paketli VPN Dosyaları Ekle", callback_data="admin_paketli_menu"))
        markup.add(types.InlineKeyboardButton("🎁 Şerit Kapak Dosyası Ekle", callback_data="add_serit_kapak"))
        markup.add(types.InlineKeyboardButton("🎗️ Şerit Dosyası Ekle", callback_data="add_serit"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("📂 Dosya Ekleme Ana Menüsü:", chat_id, call.message.message_id, reply_markup=markup)
        return

    if call.data == "admin_add_tls":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (TLS)", callback_data="add_tls_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (TLS)", callback_data="add_tls_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (TLS)", callback_data="add_tls_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (TLS)", callback_data="add_tls_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (TLS)", callback_data="add_tls_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (TLS)", callback_data="add_tls_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (TLS)", callback_data="add_tls_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="admin_paketli_menu"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🔒 **TLS Paket Seç:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "admin_add_http":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (HTTP)", callback_data="add_http_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (HTTP)", callback_data="add_http_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (HTTP)", callback_data="add_http_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (HTTP)", callback_data="add_http_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (HTTP)", callback_data="add_http_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (HTTP)", callback_data="add_http_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (HTTP)", callback_data="add_http_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="admin_paketli_menu"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🌐 **HTTP Paket Seç:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "admin_add_v2ray":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (V2Ray)", callback_data="add_v2ray_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (V2Ray)", callback_data="add_v2ray_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (V2Ray)", callback_data="add_v2ray_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (V2Ray)", callback_data="add_v2ray_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (V2Ray)", callback_data="add_v2ray_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (V2Ray)", callback_data="add_v2ray_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (V2Ray)", callback_data="add_v2ray_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="admin_paketli_menu"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🚀 **V2Ray Paket Seç:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "admin_add_npvt":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (NPVT)", callback_data="add_npvt_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (NPVT)", callback_data="add_npvt_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (NPVT)", callback_data="add_npvt_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (NPVT)", callback_data="add_npvt_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (NPVT)", callback_data="add_npvt_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (NPVT)", callback_data="add_npvt_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (NPVT)", callback_data="add_npvt_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="admin_paketli_menu"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("⚡ **NPVT Paket Seç:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "menu_paketsiz":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🟡 Turkcell (Paketsiz)", callback_data="satinal_turkcell"))
        markup.add(types.InlineKeyboardButton("🔴 Vodafone (Paketsiz)", callback_data="satinal_vodafone"))
        markup.add(types.InlineKeyboardButton("🔵 Türk Telekom (Paketsiz)", callback_data="satinal_turktelekom"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="geri_vpn_menu"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🟢 **Paketsiz VPN Menüsü (Dosya Başı 10 Puan):**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "menu_paketli":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔒 TLS Tünel (Paketli)", callback_data="sub_tls"))
        markup.add(types.InlineKeyboardButton("🌐 HTTP Custom (Paketli)", callback_data="sub_http"))
        markup.add(types.InlineKeyboardButton("🚀 V2Ray (Paketli)", callback_data="sub_v2ray"))
        markup.add(types.InlineKeyboardButton("⚡ NPVT (Paketli)", callback_data="sub_npvt"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="geri_vpn_menu"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("📦 **Paketli VPN Altyapıları:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "geri_vpn_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🟢 Paketsiz VPN'ler", callback_data="menu_paketsiz"))
        markup.add(types.InlineKeyboardButton("📦 Paketli VPN'ler", callback_data="menu_paketli"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🔐 **VPN Ana Menüsü:**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "sub_tls":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (TLS)", callback_data="satinal_tls_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (TLS)", callback_data="satinal_tls_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (TLS)", callback_data="satinal_tls_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (TLS)", callback_data="satinal_tls_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (TLS)", callback_data="satinal_tls_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (TLS)", callback_data="satinal_tls_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (TLS)", callback_data="satinal_tls_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="menu_paketli"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🔒 **TLS Paketli Servisler (10 Puan):**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "sub_http":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (HTTP)", callback_data="satinal_http_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (HTTP)", callback_data="satinal_http_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (HTTP)", callback_data="satinal_http_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (HTTP)", callback_data="satinal_http_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (HTTP)", callback_data="satinal_http_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (HTTP)", callback_data="satinal_http_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (HTTP)", callback_data="satinal_http_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="menu_paketli"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🌐 **HTTP Custom Paketli Servisler (10 Puan):**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "sub_v2ray":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (V2Ray)", callback_data="satinal_v2ray_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (V2Ray)", callback_data="satinal_v2ray_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (V2Ray)", callback_data="satinal_v2ray_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (V2Ray)", callback_data="satinal_v2ray_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (V2Ray)", callback_data="satinal_v2ray_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (V2Ray)", callback_data="satinal_v2ray_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (V2Ray)", callback_data="satinal_v2ray_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="menu_paketli"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("🚀 **V2Ray Paketli Servisler (10 Puan):**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    if call.data == "sub_npvt":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🤖 ChatGPT (NPVT)", callback_data="satinal_npvt_chatgpt"))
        markup.add(types.InlineKeyboardButton("💬 WhatsApp (NPVT)", callback_data="satinal_npvt_whatsapp"))
        markup.add(types.InlineKeyboardButton("⚡ Speedtest (NPVT)", callback_data="satinal_npvt_speedtest"))
        markup.add(types.InlineKeyboardButton("✈️ Telegram (NPVT)", callback_data="satinal_npvt_telegram"))
        markup.add(types.InlineKeyboardButton("📺 YouTube (NPVT)", callback_data="satinal_npvt_youtube"))
        markup.add(types.InlineKeyboardButton("🎵 TikTok (NPVT)", callback_data="satinal_npvt_tiktok"))
        markup.add(types.InlineKeyboardButton("📘 Facebook (NPVT)", callback_data="satinal_npvt_facebook"))
        markup.add(types.InlineKeyboardButton("⬅️ Geri Dön", callback_data="menu_paketli"))
        bot.answer_callback_query(call.id)
        bot.edit_message_text("⚡ **NPVT Paketli Servisler (10 Puan):**", chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        return

    # Satın alma onay ekranı
    if call.data.startswith("satinal_"):
        gercek_vpn = call.data.replace("satinal_", "")
        gecici_secim[user_id] = gercek_vpn
        
        market_urunleri = ["serit_kapak", "serit", "vodafone_pay", "play_kod"]
        maliyet = 200 if gercek_vpn in market_urunleri else 10
        
        mevcut_puan = get_user(user_id)

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Evet, Al", callback_data="satin_al_onay"),
            types.InlineKeyboardButton("❌ Vazgeç", callback_data="satin_al_iptal")
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            f"🛒 **Dosya Satın Alma Onayı**\n\n"
            f"• Ürün: `{gercek_vpn}.hc`\n"
            f"• Ücret: **{maliyet} Puan**\n"
            f"• Mevcut Puanın: **{mevcut_puan if not is_admin(user_id) else 'Sınırsız ♾️'}**\n\n"
            f"Bu ürünü almak istiyor musun?",
            chat_id, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
        return

    if call.data == "satin_al_onay":
        bot.answer_callback_query(call.id)
        if user_id not in gecici_secim or not gecici_secim[user_id]:
            bot.edit_message_text("⚠️ İşlem zaman aşımına uğradı, lütfen tekrar dene.", chat_id, call.message.message_id)
            return

        hedef = gecici_secim[user_id]
        market_urunleri = ["serit_kapak", "serit", "vodafone_pay", "play_kod"]
        maliyet = 200 if hedef in market_urunleri else 10
        mevcut_puan = get_user(user_id)

        if not is_admin(user_id) and mevcut_puan < maliyet:
            bot.edit_message_text(f"❌ **Yetersiz Puan!** Bu ürünü almak için {maliyet} puan gerekiyor, mevcut puanın: {mevcut_puan}.", chat_id, call.message.message_id, parse_mode="Markdown")
            return

        if not is_admin(user_id):
            update_points(user_id, -maliyet)

        gecici_secim[user_id] = None
        dosya_adi = f"{hedef}.hc"

        if os.path.exists(dosya_adi):
            bot.edit_message_text(f"✅ Satın alma onaylandı! Dosyan gönderiliyor...", chat_id, call.message.message_id)
            with open(dosya_adi, 'rb') as dosya:
                bot.send_document(chat_id, dosya, caption=f"📁 {dosya_adi}")
        else:
            bot.edit_message_text(f"⚠️ Puanın düşüldü ancak `{dosya_adi}` dosyası henüz admin tarafından yüklenmemiş. Lütfen destek ile iletişime geç.", chat_id, call.message.message_id, parse_mode="Markdown")
        return

    if call.data == "satin_al_iptal":
        gecici_secim[user_id] = None
        bot.answer_callback_query(call.id, "İşlem iptal edildi.")
        bot.edit_message_text("❌ Satın alma işlemi iptal edildi.", chat_id, call.message.message_id)
        return

    elif call.data == "task_bonus":
        success, result = check_and_update_bonus(user_id)
        if success:
            update_points(user_id, 20)
            bot.answer_callback_query(call.id, "Tebrikler, 20 puan kazandın!")
            bot.send_message(chat_id, "🎉 Günlük bonus eklendi!")
        else:
            bot.answer_callback_query(call.id, f"⚠️ Süren dolmadı! Kalan: {result}", show_alert=True)

print("Bot çalışıyor...")
bot.infinity_polling()
