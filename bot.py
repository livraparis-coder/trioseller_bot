# TRIO HUB SMM BOT — inline UI + clean chat + referrals
# lib: pyTelegramBotAPI  (pip install pyTelegramBotAPI)

import telebot
from telebot import types
import time
import re
import os  # ✅ For environment variables

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

# ---------- ephemeral state ----------
active_msg_id = {}
pending = {}
ref_counts  = {}
invited_by  = {}
last_claim  = {}

# ---------- helpers ----------

def send_or_edit(chat_id, text, reply_markup=None):
    mid = active_msg_id.get(chat_id)
    if mid:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=mid,
                text=text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        except Exception:
            pass
    m = bot.send_message(chat_id, text, reply_markup=reply_markup)
    active_msg_id[chat_id] = m.message_id

def kb_main():
    k = types.InlineKeyboardMarkup()
    k.add(types.InlineKeyboardButton("📸 Instagram Followers", callback_data="cat:followers"))
    k.add(types.InlineKeyboardButton("❤️ Instagram Likes",     callback_data="cat:likes"))
    k.add(types.InlineKeyboardButton("▶️ Instagram Views",     callback_data="cat:views"))
    k.add(types.InlineKeyboardButton("👥 Join Group",          url=GROUP_LINK))
    k.add(types.InlineKeyboardButton("☎ Support",              callback_data="support"))
    k.add(types.InlineKeyboardButton("🎯 Referral",            callback_data="ref:menu"))
    return k

def kb_plans(cat):
    k = types.InlineKeyboardMarkup()
    for idx, (name, line, _price) in enumerate(PRICES[cat]):
        k.add(types.InlineKeyboardButton(f"{name}", callback_data=f"plan:{cat}:{idx}"))
    k.add(types.InlineKeyboardButton("⬅ Back to menu", callback_data="back:main"))
    return k

def kb_after_plan(cat, idx):
    return types.InlineKeyboardMarkup().add(
        types.InlineKeyboardButton("🧾 Payment Format / Where to send", callback_data=f"format:{cat}:{idx}")
    ).add(
        types.InlineKeyboardButton("⬅ Back", callback_data=f"back:cat:{cat}")
    )

def kb_ref_menu():
    k = types.InlineKeyboardMarkup()
    k.add(types.InlineKeyboardButton("👥 My referrals", callback_data="ref:count"))
    k.add(types.InlineKeyboardButton("🔗 Copy referral link", callback_data="ref:link"))
    k.add(types.InlineKeyboardButton("🎁 Claim free 2k views", callback_data="ref:claim"))
    k.add(types.InlineKeyboardButton("🏆 Referral levels", callback_data="ref:levels"))
    k.add(types.InlineKeyboardButton("⬅ Back to menu", callback_data="back:main"))
    return k

def prettify_prices(cat, emoji, word):
    lines = [f"🚀 TRIO HUB SMM - Official Price List 🚀\n\n{emoji} {word} PACKAGES\n"]
    for _, line, _ in PRICES[cat]:
        lines.append(line)
    lines.append("\n✅ Why TRIO HUB SMM ?\nFast Delivery | Safe | 24/7 Support\n\nSelect a plan 👇")
    return "\n".join(lines)

def need_reel_note():
    return "📎 *REEL LINK only* (no profile links)\n
