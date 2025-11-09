# TRIO HUB SMM BOT — inline UI + clean chat + referrals
# lib: pyTelegramBotAPI  (pip install pyTelegramBotAPI)

import telebot
from telebot import types
import time
import re

# ✅ Direct Bot Token (you wanted this method)
BOT_TOKEN = "8311230763:AAFcBn4qxzeKF9gA7mLqmtzppCf7v-iHxKU"   # <-- REPLACE this with your real token
BOT_USERNAME = "trioseller_bot"     # without @
GROUP_LINK = "https://t.me/triosellerofficial"
PAYMENT_GROUP = "https://t.me/triohubpayment"

# ✅ UPI List
UPI_LIST = [
    "ishan7408@fam",
    "rameshzx@fam",
    "Adarshupadhyay@fam"
]

# ✅ Prices
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

REF_BONUS_VIEWS = 2000
CLAIM_COOLDOWN = 60 * 60  # 1 hour

# ✅ Initialize bot
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="Markdown")

# ✅ In-memory states
active_msg_id = {}     # chat_id -> message_id
pending = {}           # user_id -> {"cat": "likes", "plan_idx": 0}
ref_counts = {}        # user_id -> count
invited_by = {}        # referred_user_id -> inviter_id
last_claim = {}        # user_id -> epoch seconds

# ✅ Helper functions
def send_or_edit(chat_id, text, reply_markup=None):
    mid = active_msg_id.get(chat_id)
    if mid:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=mid, text=text,
                                  reply_markup=reply_markup, parse_mode="Markdown")
            return
        except Exception:
            pass
    m = bot.send_message(chat_id, text, reply_markup=reply_markup)
    active_msg_id[chat_id] = m.message_id

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
    for idx, (name, _line, _price) in enumerate(PRICES[cat]):
        k.add(types.InlineKeyboardButton(name, callback_data=f"plan:{cat}:{idx}"))
    k.add(types.InlineKeyboardButton("⬅ Back to menu", callback_data="back:main"))
    return k

def need_reel_note():
    return "📎 *REEL LINK only* (no profile links)\n⚠️ *Wrong links = NO REFUND*"

def clean_try_delete_user_message(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

# ✅ Commands
@bot.message_handler(commands=["start", "restart"])
def start_cmd(message):
    clean_try_delete_user_message(message)
    send_or_edit(message.chat.id, "Welcome to TRIO HUB SMM 🚀\nSelect a service 👇", kb_main())

# ✅ Callback Handler (Buttons Working Here)
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    data = call.data
    cid = call.message.chat.id

    if data.startswith("cat:"):
        cat = data.split(":")[1]
        send_or_edit(cid, f"Choose a {cat.capitalize()} plan 👇", kb_plans(cat))

# ✅ Run the bot
print("🤖 Bot is running…")
bot.infinity_polling(skip_pending=True)
