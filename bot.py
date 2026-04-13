from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, CallbackQueryHandler, ContextTypes
import sqlite3
import time
import os

# ================= CONFIG =================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # 🔐 secure token

ADMIN_ID = 7791039397
CHANNEL_USERNAME = "@FCBD_OFFICIAL"

PRIVATE_GROUP_LINK = "https://t.me/+WU_Qyp-jlNdjOWU1"

# ================= DATABASE =================
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER,
    name TEXT,
    course TEXT,
    time TEXT
)
""")
db.commit()

# ================= COURSES =================
COURSES = {
    "bpchem27": [("Main", -1003086203474)],
    "ftebi27": [("Main", -1002997875266)],
    "acsmath27": [("Main", -1003055177925)],
    "rmh27": [("Main", -1003162446350)],
    "himel27": [("Main", -1002790878049)],
    "acsphy27": [("Main", -1003027009834)],
    "biomission27": [("Main", -1002980602736)],
    "bhcombo27": [("Main", -1002744441828)],
    "paveleng27": [("Main", -1002931164859)],
    "aloron27": [("Main", -1002694694233)],
    "sumoneng27": [("Main", -1003567141118)],
    "udvashict27": [("Main", -1002922998471)],
    "udvashbaneng27": [("Main", -1003045975038)],
    "udvash1styear27": [("Main", -1003176489421)],
    "pos1st27": [("Main", -1003164807621)],
    "acsict27": [("Main", -1002970710019)],

    "acs27 combo": [
        ("Physics", -1003027009834),
        ("Chemistry", -1002790878049),
        ("Math", -1003055177925),
        ("Biology", -1002980602736),
    ]
}

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/FCBD_OFFICIAL")],
        [InlineKeyboardButton("✅ Joined", callback_data="check_join")]
    ]
    await update.message.reply_text(
        "🚫 আগে আমাদের চ্যানেলে জয়েন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= MAIN MENU =================
async def mainmenu(message, context):
    await message.reply_text(
        "📩 নিচের ফরমেটে আপনার তথ্য দিন:\n\n"
        "Course : Course Name\n"
        "Number : 01XXXXXXXXX\n"
        "Trx Id : XXXXX"
    )

# ================= CHECK JOIN =================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(CHANNEL_USERNAME, user_id)

        if member.status in ["member", "administrator", "creator"]:
            await query.answer()
            await query.message.reply_text("🎉 Welcome! এখন তথ্য দিন নিচের ফরমেটে 👇")
            await mainmenu(query.message, context)
        else:
            await query.answer("❌ আগে চ্যানেলে জয়েন করুন!", show_alert=True)

    except:
        await query.answer("⚠️ Error!", show_alert=True)

# ================= HANDLE PAYMENT =================
async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text.lower()

    selected_course = None

    for line in text.split("\n"):
        if "course" in line:
            selected_course = line.replace("course", "").replace(":", "").strip()

    if not selected_course or selected_course not in COURSES:
        await update.message.reply_text("❌ Course not found!")
        return

    await update.message.reply_text("⏳ অপেক্ষা করুন...")

    keyboard = [
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}_{selected_course}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 Payment Request\n\n👤 {user.first_name}\n🆔 {user.id}\n\n{text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= APPROVE / REJECT =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split("_")
    action = data[0]
    user_id = int(data[1])

    if action == "approve":
        course = data[2]
        groups = COURSES[course]

        all_links = ""
        expire_time = int(time.time()) + 86400  # 24h

        for name, gid in groups:
            try:
                link = await context.bot.create_chat_invite_link(
                    chat_id=gid,
                    member_limit=1,
                    expire_date=expire_time
                )
                all_links += f"🔹 {name}: {link.invite_link}\n"
            except:
                all_links += f"❌ {name}: Failed\n"

        # save user
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?)",
            (user_id, query.from_user.first_name, course, time.ctime())
        )
        db.commit()

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                f"✅ Payment Approved!\n\n"
                f"🔗 Main Group:\n{PRIVATE_GROUP_LINK}\n\n"
                f"📚 Course Links:\n{all_links}\n"
                f"⏰ Link valid: 24 hours\n"
            )
        )

        await query.message.reply_text("✅ Approved")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Payment rejected"
        )
        await query.message.reply_text("❌ Rejected")

# ================= USER HISTORY =================
async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    cursor.execute("SELECT course, time FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchall()

    if not data:
        await update.message.reply_text("❌ কোনো history পাওয়া যায়নি")
        return

    msg = "📜 Your Purchase History:\n\n"
    for course, t in data:
        msg += f"📚 {course} | 🕒 {t}\n"

    await update.message.reply_text(msg)

# ================= ADMIN =================
async def all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT * FROM users")
    data = cursor.fetchall()

    if not data:
        await update.message.reply_text("❌ No data found")
        return

    msg = "📊 All Users Data:\n\n"

    for user_id, name, course, t in data:
        msg += f"👤 {name} ({user_id})\n📚 {course}\n🕒 {t}\n\n"

    await update.message.reply_text(msg)

# ================= RUN =================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("history", history))
app.add_handler(CommandHandler("users", all_users))

app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
app.add_handler(CallbackQueryHandler(button_handler))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_payment))

print("✅ Bot is running...")
app.run_polling()
