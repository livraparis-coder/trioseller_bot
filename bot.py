# TRIO HUB SMM BOT — inline UI + clean chat + referrals
# lib: pyTelegramBotAPI  (pip install pyTelegramBotAPI)

import telebot
from telebot import types
import time
import re

BOT_TOKEN     = "8311230763:AAFcBn4qxzeKF9gA7mLqmtzppCf7v-iHxKU"
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

# ---------- ephemeral state (in-memory) ----------
# one active message per chat to keep it clean
active_msg_id = {}        # chat_id -> message_id
# per-user temp selection for buy flow
pending = {}              # user_id -> {"cat": "likes", "plan_idx": 0}
# referral bookkeeping
ref_counts  = {}          # user_id -> count
invited_by  = {}          # referred_user_id -> inviter_id
last_claim  = {}          # user_id -> epoch seconds

# ---------- helpers ----------

def send_or_edit(chat_id, text, reply_markup=None):
    """Keep one message on screen: edit if exists, else send new."""
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
            # message might be gone; fall through to send a new one
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

def prettify_prices(cat, title_emoji, title_word):
    lines = [f"🚀 TRIO HUB SMM - Official Price List 🚀\n\n{title_emoji} {title_word} PACKAGES\n"]
    for name, line, _ in PRICES[cat]:
        lines.append(f"{line}")
    lines.append("\n✅ Why TRIO HUB SMM ?\nFast Delivery | Safe | 24/7 Support\n\nSelect a plan 👇")
    return "\n".join(lines)

def need_reel_note():
    return "📎 *REEL LINK only* (no profile links)\n⚠️ *Wrong links = NO REFUND*"

def clean_try_delete_user_message(message):
    # Try to delete the user message that triggered a command (works in many clients)
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass

# ---------- commands ----------

@bot.message_handler(commands=["start","restart"])
def start_cmd(message):
    clean_try_delete_user_message(message)

    # deep-link ref: /start ref_123 or /start ref_123 with/without space
    payload = None
    if message.text.startswith("/start"):
        m = re.search(r"ref_(\d+)", message.text)
        if m:
            inviter = int(m.group(1))
            uid = message.from_user.id
            if inviter != uid and uid not in invited_by:
                invited_by[uid] = inviter
                ref_counts[inviter] = ref_counts.get(inviter, 0) + 1

    send_or_edit(
        message.chat.id,
        "Welcome to TRIO HUB SMM 🚀\nSelect a service 👇",
        kb_main()
    )

@bot.message_handler(commands=["help"])
def help_cmd(message):
    clean_try_delete_user_message(message)
    text = (
        "❓ *Help & Support*\n\n"
        "Choose a category, pick a plan, pay via UPI, and post proof in the payment group.\n\n"
        "*Commands:*\n"
        "/start — Start the bot\n"
        "/restart — Open main menu\n"
        "/help — Show this help\n"
        "/group — Join our group\n"
        "/support — Contact support\n"
        "/clear — Clear bot messages here"
    )
    send_or_edit(message.chat.id, text, kb_main())

@bot.message_handler(commands=["group"])
def group_cmd(message):
    clean_try_delete_user_message(message)
    send_or_edit(message.chat.id, f"👥 Join Group: {GROUP_LINK}", kb_main())

@bot.message_handler(commands=["support"])
def support_cmd(message):
    clean_try_delete_user_message(message)
    send_or_edit(message.chat.id, "☎ Support coming soon (WhatsApp link to be added).", kb_main())

@bot.message_handler(commands=["clear"])
def clear_cmd(message):
    # In private chats we can delete our own messages; we also try to delete the user’s last command
    clean_try_delete_user_message(message)
    cid = message.chat.id
    mid = active_msg_id.get(cid)
    if mid:
        try:
            bot.delete_message(cid, mid)
        except Exception:
            pass
        active_msg_id.pop(cid, None)
    # Show a fresh menu
    send_or_edit(cid, "Chat cleared ✅\n\nWelcome to TRIO HUB SMM 🚀\nSelect a service 👇", kb_main())

# ---------- callbacks (inline buttons) ----------

@bot.callback_query_handler(func=lambda c: True)
def on_cb(cb: types.CallbackQuery):
    data = cb.data
    cid  = cb.message.chat.id
    uid  = cb.from_user.id

    # category
    if data.startswith("cat:"):
        cat = data.split(":")[1]
        titles = {"likes":("❤️","LIKE"),"followers":("⭐","FOLLOWER"),"views":("📈","VIEWS")}
        emoji, word = titles[cat]
        text = prettify_prices(cat, emoji, word)
        send_or_edit(cid, text, kb_plans(cat))

    # back
    elif data == "back:main":
        send_or_edit(cid, "Welcome to TRIO HUB SMM 🚀\nSelect a service 👇", kb_main())

    elif data.startswith("back:cat:"):
        cat = data.split(":")[2]
        titles = {"likes":("❤️","LIKE"),"followers":("⭐","FOLLOWER"),"views":("📈","VIEWS")}
        emoji, word = titles[cat]
        text = prettify_prices(cat, emoji, word)
        send_or_edit(cid, text, kb_plans(cat))

    # plan chosen
    elif data.startswith("plan:"):
        _, cat, idxs = data.split(":")
        idx = int(idxs)
        name, line, amount = PRICES[cat][idx]
        pending[uid] = {"cat":cat, "plan_idx":idx}

        upis = "\n".join(f"`{u}`" for u in UPI_LIST)
        body = (
            f"✅ *You selected:* {name} {cat.capitalize()}\n"
            f"💰 *Price:* {line.split('=')[1].strip()}\n\n"
            f"💳 *Pay to ANY UPI below:*\n{upis}\n\n"
            "📤 After payment, post proof in the payment group and follow the exact format.\n"
            f"📎 *Payment Proof Group:* {PAYMENT_GROUP}\n\n"
            "🧾 *Format to post:*\n"
            f"Paid: ₹{amount}\n"
            f"For: {name} {cat}\n"
            "REEL LINK (only)\n\n"
            + need_reel_note()
        )
        send_or_edit(cid, body, kb_after_plan(cat, idx))

    # show format (same message, just re-show)
    elif data.startswith("format:"):
        _, cat, idxs = data.split(":")
        idx = int(idxs)
        name, _line, amount = PRICES[cat][idx]
        upis = "\n".join(f"`{u}`" for u in UPI_LIST)
        body = (
            f"🧾 *Payment Format*\n\n"
            f"Pay any UPI:\n{upis}\n\n"
            "Post in payment group with:\n"
            f"Paid: ₹{amount}\n"
            f"For: {name} {cat}\n"
            "REEL LINK (only)\n\n"
            + need_reel_note() + f"\n\nPayment Group: {PAYMENT_GROUP}"
        )
        send_or_edit(cid, body, kb_after_plan(cat, idx))

    # support
    elif data == "support":
        send_or_edit(cid, "☎ Support coming soon. You can also join the group:", 
                     types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("👥 Join Group", url=GROUP_LINK)
                     ).add(
                         types.InlineKeyboardButton("⬅ Back to menu", callback_data="back:main")
                     ))

    # referrals
    elif data == "ref:menu":
        count = ref_counts.get(uid, 0)
        link  = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
        k = kb_ref_menu()
        text = (f"🎯 *Referral Center*\n\n"
                f"• Your referrals: *{count}*\n"
                f"• Reward: *{REF_BONUS_VIEWS} views per referral*\n\n"
                f"Your link:\n`{link}`\n\n"
                "Invite friends — when they press Start via your link, you get credit.")
        send_or_edit(cid, text, k)

    elif data == "ref:count":
        count = ref_counts.get(uid, 0)
        send_or_edit(cid, f"👥 You have *{count}* referral(s). Keep going! 🎉",
                     types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("⬅ Back to referrals", callback_data="ref:menu")
                     ))

    elif data == "ref:link":
        link  = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}"
        send_or_edit(cid, f"🔗 Your referral link:\n`{link}`",
                     types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("⬅ Back to referrals", callback_data="ref:menu")
                     ))

    elif data == "ref:levels":
        txt = ("🏆 *Referral Levels (Views you can claim)*\n\n"
               "1 Referral → 2,000 views\n"
               "2 Referrals → 4,000 views\n"
               "3 Referrals → 6,000 views\n"
               "4 Referrals → 8,000 views\n"
               "5 Referrals → 10,000 views\n\n"
               "Use *Claim free 2k views* to redeem.")
        send_or_edit(cid, txt,
                     types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("⬅ Back to referrals", callback_data="ref:menu")
                     ))

    elif data == "ref:claim":
        count = ref_counts.get(uid, 0)
        now   = int(time.time())
        lc    = last_claim.get(uid, 0)
        if count <= 0:
            send_or_edit(cid, "❌ You have no referrals to claim.", 
                         types.InlineKeyboardMarkup().add(
                             types.InlineKeyboardButton("⬅ Back to referrals", callback_data="ref:menu")
                         ))
            return
        if now - lc < CLAIM_COOLDOWN:
            mins = (CLAIM_COOLDOWN - (now - lc)) // 60
            send_or_edit(cid, f"⏳ Please wait *{mins} min* before claiming again.",
                         types.InlineKeyboardMarkup().add(
                             types.InlineKeyboardButton("⬅ Back to referrals", callback_data="ref:menu")
                         ))
            return
        # ask for reel link via ForceReply
        force = types.ForceReply(input_field_placeholder="Paste REEL LINK here (only)")
        m = bot.send_message(cid, "Paste your *REEL LINK* to redeem 2k views (1 referral will be deducted):", reply_markup=force)
        active_msg_id[cid] = m.message_id  # keep one message

# handle the reply with the reel link for referral claim
@bot.message_handler(func=lambda m: m.reply_to_message and "redeem 2k views" in (m.reply_to_message.text or ""))
def ref_claim_reel(message):
    cid = message.chat.id
    uid = message.from_user.id
    link = (message.text or "").strip()

    # delete user's link message to keep clean
    clean_try_delete_user_message(message)

    if not ("instagram.com" in link and "reel" in link):
        send_or_edit(cid, "❌ Invalid link.\n" + need_reel_note(),
                     types.InlineKeyboardMarkup().add(
                         types.InlineKeyboardButton("⬅ Back to referrals", callback_data="ref:menu")
                     ))
        return

    # deduct & cooldown
    ref_counts[uid]  = ref_counts.get(uid, 0) - 1
    if ref_counts[uid] < 0:
        ref_counts[uid] = 0
    last_claim[uid]  = int(time.time())

    # send to payment group with required format
    try:
        bot.send_message(PAYMENT_GROUP, f"REEL LINK: {link}\nREFERRAL PLAN: 2k views (1 referral)")
    except Exception:
        # if PAYMENT_GROUP is private without the bot, nothing we can do
        pass

    send_or_edit(cid, "✅ Referral claim submitted!\nPlease wait for delivery. 🙌",
                 types.InlineKeyboardMarkup().add(
                     types.InlineKeyboardButton("⬅ Back to menu", callback_data="back:main")
                 ))

# ---------- run ----------
print("🤖 TRIO HUB SMM bot running…")
bot.infinity_polling(skip_pending=True)
