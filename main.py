import logging, sqlite3, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8754917421
BKASH_NUMBER = "01764201670"
NAGAD_NUMBER = "01764201670"

conn = sqlite3.connect("nova.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0, refer_by INTEGER, active INTEGER DEFAULT 0, refer_count INTEGER DEFAULT 0)")
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    refer_by = int(args[0]) if args and args[0].isdigit() else None
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id=?", (user.id,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users (id, refer_by) VALUES (?,?)", (user.id, refer_by))
        conn.commit()
    keyboard = [
        [InlineKeyboardButton("💰 Active Account (100৳)", callback_data="active")],
        [InlineKeyboardButton("👥 My Refer Link", callback_data="refer"), InlineKeyboardButton("💵 Balance", callback_data="balance")],
        [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw"), InlineKeyboardButton("📞 Support", url="https://t.me/nova_refer_earn")]
    ]
    text = f"🚀 **Welcome {user.first_name} to NOVA Refer Earn!**\n\n💵 100 Taka দিয়ে Active করুন\n👥 প্রতি রেফারে 20 Taka\n💳 Withdraw: Bkash/Nagad"
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    cur = conn.cursor()
    if query.data == "active":
        await query.message.reply_text(f"💳 **Payment করুন:**\n\nBkash Personal: `{BKASH_NUMBER}`\nNagad Personal: `{NAGAD_NUMBER}`\n\n100৳ Send Money করে TrxID টা এখানে পাঠান।", parse_mode="Markdown")
    elif query.data == "refer":
        cur.execute("SELECT active FROM users WHERE id=?", (uid,))
        row = cur.fetchone()
        if not row or row[0]==0:
            await query.message.reply_text("❌ আগে Account Active করুন 100৳ দিয়ে!")
            return
        link = f"https://t.me/nova_refer_earn_bot?start={uid}"
        await query.message.reply_text(f"👥 **তোমার Refer Link:**\n{link}", parse_mode="Markdown")
    elif query.data == "balance":
        cur.execute("SELECT balance, refer_count FROM users WHERE id=?", (uid,))
        b,c = cur.fetchone() or (0,0)
        await query.message.reply_text(f"💰 Balance: {b}৳\n👥 Total Refer: {c} জন")
    elif query.data == "withdraw":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = (cur.fetchone() or [0])[0]
        if bal < 100:
            await query.message.reply_text(f"❌ Minimum 100৳। তোমার আছে {bal}৳")
        else:
            await query.message.reply_text("💳 Withdraw এর জন্য লিখো:\n`Bkash 01764201670 150`", parse_mode="Markdown")

async def handle_trx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    trx = update.message.text.strip()
    if len(trx) < 6: return
    await context.bot.send_message(ADMIN_ID, f"🔔 New Payment\nUser: {update.effective_user.id}\nTrxID: {trx}\n\nApprove: /approve {update.effective_user.id}")
    await update.message.reply_text("✅ TrxID পেয়েছি! Admin 5 মিনিটে Active করে দিবে।")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID: return
    try:
        uid = int(context.args[0])
        cur = conn.cursor()
        cur.execute("SELECT refer_by, active FROM users WHERE id=?", (uid,))
        row = cur.fetchone()
        if row and row[1]==0:
            cur.execute("UPDATE users SET active=1 WHERE id=?", (uid,))
            if row[0]:
                cur.execute("UPDATE users SET balance=balance+20, refer_count=refer_count+1 WHERE id=?", (row[0],))
                try: await context.bot.send_message(row[0], f"🎉 তোমার রেফারে {uid} Active হয়েছে! 20৳ বোনাস!")
                except: pass
            conn.commit()
            await update.message.reply_text(f"✅ {uid} Active Done!")
            await context.bot.send_message(uid, "🎉 Congratulations! Your Account Active!")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_trx))
app.run_polling()
