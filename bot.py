# TRIO HUB SMM BOT — inline UI + clean chat + referrals
# lib: pyTelegramBotAPI  (pip install pyTelegramBotAPI)

import telebot
from telebot import types
import time
import re
import os  # ✅ For environment variables

# ✅ Secure Bot Token from Render/Environment
BOT_TOKEN = os.getenv("8311230763:AAFcBn4qxzeKF9gA7mLqmtzppCf7v-iHxKU")  # Must be added in Render → Environment Variables

# ✅ Required data
BOT_USERNAME = "trioseller_bot"  # without @
GROUP_LINK = "https://t.me/triosellerofficial"
PAYMENT_GROUP = "https://t.me/triohubpayment"

UPI_LIST = [
    "ishan7408@fam",
    "rameshzx@fam",
    "Adarshupadhyay@fam"
]

# ✅ Prices (Already 50% OFF)
PRICES = {
    "followers": [
        ("🥉 Bronze", "1k Followers = ₹99", 99),
        ("🥈 Silver", "5k Followers = ₹349", 349),
        ("🥇 Gold", "10k Followers = ₹599", 599),
        ("💎 Platinum", "50k Followers = ₹3999", 3999)
    ],
    "likes": [
        ("🥉 Bronze", "1k Likes = ₹29", 29),
        ("🥈 Silver", "5k Likes = ₹119", 119),
        ("🥇 Gold", "10k Likes = ₹199", 199),
        ("💎 Platinum", "100k Likes = ₹1499", 1499)
    ],
    "views": [
        ("🥉 Bronze", "1k Views = ₹5", 5),
        ("🥈 Silver", "10k Views = ₹9 (🔥 BEST VALUE!)", 9),
        ("🥇 Gold", "100k Views = ₹39", 39),
        ("💎 Platinum", "1M Views = ₹299", 299)
    ]
}

# ✅ Referral system
REF_BONUS_VIEWS = 2000
CLAIM_COOLDOWN = 3600  # 1 hour

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# Temporary Memory Data
active_msg_id = {}   # chat_id -> message_id
pending = {}         # user_id -> {"cat": "", "plan_idx": 0}
ref_counts = {}      # user_id -> referral count
invited_by = {}      # user_id -> inviter_id
last_claim = {}      # user_id -> timestamp

# ---------- Helper Functions ----------

def send_or_edit(chat_id, text, reply_markup=None):
    mid = active_msg_id.get(chat_id)
    if mid:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=mid, text=text, reply_markup=reply_markup)
            return
        except Exception:
            pass
    m = bot.send_message(chat_id, text, reply_markup=reply_markup)
    active_msg_id[chat_id] = m.message_id

def clean_try_delete(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

def kb_main():
    k = types.InlineKeyboardMarkup()
    k.add(types.InlineKeyboardButton("📸 Instagram Followers", callback_data="cat:followers"))
    k.add(types.InlineKeyboardButton("❤️ Instagram Likes", callback_data="cat:likes"))
    k.add(types.InlineKeyboardButton("▶️ Instagram Views", callback_data="cat:views"))
    k.add(types.InlineKeyboardButton("👥 Join Group", url=GROUP_LINK))
    k.add(types.InlineKeyboardButton("☎ Support", callback_data="support"))
    k.add(types.InlineKeyboardButton("🎯 Referral", callback_data="ref:menu"))
    return k

def kb_plans(cat):
    k = types.InlineKeyboardMarkup()
    for idx, (name, _, _) in enumerate(PRICES[cat]):
        k.add(types.InlineKeyboardButton(name, callback_data=f"plan:{cat}:{idx}"))
    k.add(types.InlineKeyboardButton("⬅ Back to Menu", callback_data="back:main"))
    return k

def need_reel_note():
    return "📎 *REEL LINK only* (no profile links)\n⚠️ *Wrong links = NO REFUND*"

# ---------- Commands ----------

@bot.message_handler(commands=["start", "restart"])
def start_cmd(message):
    clean_try_delete(message)
    text = "🎉 *Welcome to TRIO HUB SMM Bot!*\nAll prices you see are already **50% OFF** for a limited time.\n\nSelect a service 👇"
    send_or_edit(message.chat.id, text, kb_main())

@bot.message_handler(commands=["clear"])
def clear_cmd(message):
    clean_try_delete(message)
    cid = message.chat.id
    if cid in active_msg_id:
        try:
            bot.delete_message(cid, active_msg_id[cid])
        except:
            pass
    active_msg_id.pop(cid, None)
    send_or_edit(cid, "✅ Chat cleared!\n\nSelect a service 👇", kb_main())

# ---------- Callback Handling ----------

@bot.callback_query_handler(func=lambda c: True)
def callback_handler(cb):
    data = cb.data
    cid = cb.message.chat.id
    uid = cb.from_user.id

    if data.startswith("cat:"):
        cat = data.split(":")[1]
        text = f"📌 Select a plan for *{cat.capitalize()}* 👇"
        send_or_edit(cid, text, kb_plans(cat))

    elif data.startswith("plan:"):
        _, cat, idx = data.split(":")
        idx = int(idx)
        name, line, amount = PRICES[cat][idx]
        upis = "\n".join(f"`{u}`" for u in UPI_LIST)
        text = f"""
✅ *Selected:* {name} ({cat})
💰 *Price:* {line.split('=')[1].strip()}

💳 *Pay to any UPI:*
{upis}

📤 After payment, post in {PAYMENT_GROUP}

🧾 *Format:*
Paid: ₹{amount}
For: {name} {cat}
REEL LINK (only)

{need_reel_note()}
"""
        send_or_edit(cid, text)

    elif data == "back:main":
        send_or_edit(cid, "🏠 Back to main menu", kb_main())

# Run bot
print("🤖 Bot is running...")
bot.infinity_polling(skip_pending=True)
