from pathlib import Path
from dotenv import load_dotenv
import os
from javascript import require, On, Once, AsyncTask, once, off

mineflayer = require("mineflayer")


# --- Configs ---

running = False

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
VERSION = os.getenv("MINECRAFT_VERSION")

name = 'Digger'


# --- Essentials ---

bot = mineflayer.createBot({
    "username": name,
    "host": HOST,
    "port": PORT,
    "version": VERSION,
    "hideErrors": False
})

@On(bot, "login")
def login():
    bot_socket = bot._client.socket
    print(
        f"[INFO]: Logged in to {bot_socket.server if bot_socket.server else bot_socket._host }"
    )

@On(bot, "kicked")
def kicked(reason, loggedIn):
    if loggedIn:
        print(f"[INFO]: Kicked from server: {reason}")
    else:
        print(f"[INFO]: Kicked whilst trying to connect: {reason}")

@On(bot, "end")
def end(reason):
    print(f"[INFO]: Disconnected: {reason}")

    off(bot, "login", login)
    off(bot, "kicked", kicked)
    off(bot, "end", end)


# --- Message Trigger ---

@On(bot, "messagestr")
def messagestr(this, message, messagePosition, jsonMsg, sender, verified):
    if messagePosition == 'Chat' and (len(message) > 4+len(name) and message[0:4+len(name)] == 'bot ' + name):
        if message == 'quit':
            this.quit()
        else:
            print(f'{sender} just said: {message}')