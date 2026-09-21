from pathlib import Path
from dotenv import load_dotenv
import os
from javascript import require, On, Once, AsyncTask, once, off
from env import MinecraftEnv

mineflayer = require("mineflayer")


# --- Configs ---

running = False

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(env_path)

NAME = os.getenv("BOTNAME")
RANGE = int(os.getenv("RANGE"))
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
def login(this):
    bot_socket = bot._client.socket
    print(
        f"[INFO]: Logged in to {bot_socket.server if bot_socket.server else bot_socket._host }"
    )

@On(bot, "kicked")
def kicked(this, reason, loggedIn):
    if loggedIn:
        print(f"[INFO]: Kicked from server: {reason}")
    else:
        print(f"[INFO]: Kicked whilst trying to connect: {reason}")

@On(bot, "end")
def end(this, reason):
    print(f"[INFO]: Disconnected: {reason}")

    off(bot, "login", login)
    off(bot, "kicked", kicked)
    off(bot, "end", end)


# --- Essential Events ---

@On(bot, "death")
def death(this):
    print(f"[INFO]: Episode {environment.episode} just finished!")

    environment.on_death(get_state())

    if environment.limit_reached:
        global running
        running = False
        print('Episode Limit reached')
        this.quit()


# --- Message Trigger ---

@On(bot, "messagestr")
def messagestr(this, message, messagePosition, jsonMsg, sender, verified=None):
    if messagePosition != "chat":
        return

    prefix = f"bot {NAME}"

    if len(message.split(' ')) > 3 and message.split(' ')[1] == 'bot' and message.split(' ')[2] == NAME:
        command = message.split(prefix, 1)[1].strip()

        global running

        if command == "quit":
            this.quit()
        elif command == "run":
            running = True
        elif command == "stop":
            running = False
            bot.clearControlStates()
        else:
            print(f"{message.split(' ')[0][1:-1]} just said: {command}")


# --- Main Area ---

environment = MinecraftEnv(grid_radius=RANGE)

def execute():
    if running:
        action = environment.on_tick(get_state())
        perform_action(action)

tick_counter = 0

@On(bot, "physicsTick")
def on_tick(this):
    global tick_counter

    tick_counter += 1

    if tick_counter >= environment.tick_every:
        tick_counter = 0
        execute()


def perform_action(action):
    bot.clearControlStates()
    
    # move
    if "controls" in action:
        for control in action["controls"]:
            bot.setControlState(control, True)

    # look around
    if "dyaw" in action or "dpitch" in action:
        bot.look(
            bot.entity.yaw + action.get("dyaw", 0),
            bot.entity.pitch + action.get("dpitch", 0),
        )

    # attack
    if "attack" in action:
        target = bot.entityAtCursor(RANGE)
        if target:
            bot.attack(target)
        else:
            bot.swingArm('right')   


UNKNOWN_BLOCK = "unknown"

def get_state():
    entity = bot.entity
    return {
        "position": vector_to_tuple(entity.position),
        "velocity": vector_to_tuple(entity.velocity),
        "yaw": entity.yaw,
        "pitch": entity.pitch,
        "on_ground": entity.onGround,
        "health": bot.health,
        "food": bot.food,
        "blocks": get_block_grid(environment.grid_radius),
    }

def vector_to_tuple(vector):
    return (vector.x, vector.y, vector.z)

def get_block_grid(radius):
    center = bot.entity.position.floored()
    offsets = range(-radius, radius + 1)
    return [
        [
            [get_block_name(center.offset(dx, dy, dz)) for dz in offsets]
            for dy in offsets
        ]
        for dx in offsets
    ]

def get_block_name(position):
    block = bot.blockAt(position)
    return block.name if block else UNKNOWN_BLOCK