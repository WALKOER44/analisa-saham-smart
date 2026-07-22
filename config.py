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

# Mode Local vs Online (Railway/Production)
# Ketika IS_LOCAL=True, bot tidak akan menjalankan scheduler/polling Telegram
# dan akan mengarahkan output ke LLM lokal (Ollama / LM Studio / OpenAI-compatible)
IS_LOCAL = os.getenv("IS_LOCAL", "False").strip().lower() in ("true", "1", "yes")

# Local LLM Configuration (hanya dipakai ketika IS_LOCAL=True)
LOCAL_LLM_ENDPOINT = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434")  # Ollama default
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3.2")                     # Model name