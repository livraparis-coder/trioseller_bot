# TRIO HUB SMM BOT — inline UI + clean chat + referrals
# lib: pyTelegramBotAPI  (pip install pyTelegramBotAPI)

import telebot
from telebot import types
import time
import re
import os  # For environment variables

# ✅ Secure Bot Token from Render/Environment
BOT_TOKEN = os.getenv("8311230763:AAFcBn4qxzeKF9gA7mLqmtzppCf7v-iHxKU")

BOT_USERNAME  = "trioseller_bot"  # without @
GROUP_LINK    = "https://t.me/triosellerofficial"
PAYMENT_GROUP = "https://t.me/triohubpayment"

UPI_LIST = [
    "ishan7408@fam",
    "rameshzx@fam",
    "Adarshupadhyay@fam"
]

# Prices
PRICES = {
    "followers": [("🥉 Bronze", "1k Followers = ₹99", 99),
                  ("🥈 Silver",  "5k Followers = ₹349", 349),
                  ("🥇 Gold",    "10k Followers = ₹599", 599),
                  ("💎 Platinum","50k Followers = ₹3999", 3999)],
    "likes":     [("🥉 Bronze", "1k Likes = ₹29", 29),
                  ("🥈 Silver",  "5k Likes = ₹119", 119),
                  ("🥇 Gold",    "10k Likes = ₹199", 199),
                  ("💎 Platinum","100k Likes = ₹1499", 1499)],
    "views":     [("🥉 Bronze", "1k Views = ₹5", 5),
                  ("🥈 Silver",  "10k Views = ₹9 (🔥 BEST VALUE!)", 9),
                  ("🥇 Gold",    "100k Views = ₹39", 39),
                  ("💎 Platinum","1M Views = ₹299", 299)],
}

REF_BONUS_VIEWS = 2000
CLAIM_COOLDOWN  = 60 * 60  # 1 hour

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ---------- In-Memory Data ----------
active_msg_id = {}      # chat_id -> message_id
pending = {}            # for temp plan selection
ref_counts = {}         # user_id -> count
invited_by = {}         # user_id -> inviter_id
last_claim = {}         # user_id -> time

# ---------- Helpers ----------

def send_or_edit(chat_id, text, reply_markup=None):
    mid = active_msg_id.get(chat_id)
    if mid:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=mid, text=text, reply_markup=reply_markup)
            return
        except:
            pass
    m = bot.send_message(chat_id, text, reply_markup=reply_markup)
    active_msg_id[chat_id] = m.message_id

def clean_try_delete(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

# ---------- Keyboards ----------

def kb_main():
    k = types.InlineKeyboardMarkup()
    k.add(types.InlineKeyboardButton("📸 Followers", callback_data="cat:followers"))
    k.add(types.InlineKeyboardButton("❤️ Likes", callback_data="cat:likes"))
    k.add(types.InlineKeyboardButton("▶️ Views", callback_data="cat:views"))
    k.add(types.InlineKeyboardButton("🎯 Referral", callback_data="ref:menu"))
    k.add(types.InlineKeyboardButton("☎ Support", callback_data="support"))
    k.add(types.InlineKeyboardButton("👥 Join Group", url=GROUP_LINK))
    return k

def kb_plans(cat):
    k = types.InlineKeyboardMarkup()
    for idx, (name, _, _) in enumerate(PRICES[cat]):
        k.add(types.InlineKeyboardButton(name, callback_data=f"plan:{cat}:{idx}"))
    k.add(types.InlineKeyboardButton("⬅ Back", callback_data="back:main"))
    return k

# ---------- Commands ----------

@bot.message_handler(commands=["start","restart"])
def start_cmd(message):
    clean_try_delete(message)

    if "ref_" in message.text:
        try:
            ref_id = int(message.text.split("ref_")[1])
            uid = message.from_user.id
            if uid not in invited_by and ref_id != uid:
                invited_by[uid] = ref_id
                ref_counts[ref_id] = ref_counts.get(ref_id, 0) + 1
        except:
            pass

    send_or_edit(message.chat.id, "Welcome to TRIO HUB SMM 🚀\nSelect a service 👇", kb_main())

@bot.message_handler(commands=["clear"])
def clear_cmd(message):
    clean_try_delete(message)
    cid = message.chat.id
    if active_msg_id.get(cid):
        try:
            bot.delete_message(cid, active_msg_id[cid])
        except:
            pass
        active_msg_id.pop(cid, None)
    send_or_edit(cid, "✅ Chat cleared!\n\nWelcome back 👇", kb_main())

# ---------- Callback Handler ----------

@bot.callback_query_handler(func=lambda c: True)
def on_callback(cb):
    data = cb.data
    cid = cb.message.chat.id
    uid = cb.from_user.id

    if data.startswith("cat:"):
        cat = data.split(":")[1]
        text = f"📌 Available {cat.capitalize()} Plans:\n\n" + "\n".join(f"{p[1]}" for p in PRICES[cat])
        send_or_edit(cid, text, kb_plans(cat))

    elif data == "back:main":
        send_or_edit(cid, "Welcome to TRIO HUB SMM 🚀\nSelect a service 👇", kb_main())

    elif data == "support":
        send_or_edit(cid, "☎ Support: @yourusername\nOr join group below.", 
                     types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅ Back", callback_data="back:main")))

# ---------- Run Bot ----------
print("🤖 Bot is running…")
bot.infinity_polling(skip_pending=True)
