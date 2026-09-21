from pathlib import Path
from dotenv import load_dotenv
import os
from javascript import require, On, Once, AsyncTask, once, off

mineflayer = require("mineflayer")


# --- Configs ---

running = False

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

NAME = os.getenv("BOTNAME")
HOST = os.getenv("HOST")
PORT = os.getenv("PORT")
VERSION = os.getenv("MINECRAFT_VERSION")


# --- Essentials Connection things ---

bot = mineflayer.createBot({
    "username": NAME,
    "host": HOST,
    "port": PORT,
    "version": VERSION,
    "hideErrors": True
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


# --- Essential Events ---

@On(bot, "death")
def death():
    print("I just died!")


# --- Message Trigger ---

@On(bot, "messagestr")
def messagestr(message, messagePosition, jsonMsg, sender, verified=None):
    if messagePosition != "chat":
        return

    prefix = f"bot {NAME}"

    if len(message.split(' ')) > 3 and message.split(' ')[1] == 'bot' and message.split(' ')[2] == NAME:
        command = message.split(prefix, 1)[1].strip()

        global running

        if command == "quit":
            bot.quit()
        elif command == "run":
            running = True
        elif command == "stop":
            running = False
        else:
            print(f"{message.split(' ')[0][1:-1]} just said: {command}")