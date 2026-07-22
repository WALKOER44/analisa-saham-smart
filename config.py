import os 
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TOKEN = os.getenv("TOKEN")                 # Bot Token dari @BotFather
CHAT_ID = os.getenv("CHAT_ID")             # Chat ID (user/group, support -100xxxxx)
API_KEY = os.getenv("API_KEY")             # API Key eksternal

# Aliases untuk kompatibilitas
TELEGRAM_BOT_TOKEN = TOKEN
TELEGRAM_CHAT_ID = CHAT_ID