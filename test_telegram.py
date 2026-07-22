import requests
from config import TOKEN, CHAT_ID

def send_test_message():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    
    data = {
        "chat_id": CHAT_ID,
        "text": "✅ Bot kamu berhasil jalan!"
    }

    response = requests.post(url, data=data)
    res = response.json()

    print("Status:", response.status_code)

    if res.get("ok"):
        chat = res["result"]["chat"]
        username = chat.get("username") or chat.get("first_name", "-")
        print("Username:", username)
        print("Chat ID:", chat["id"])
    else:
        print("[ERROR] Gagal:", res.get("description"))

if __name__ == "__main__":
    send_test_message()