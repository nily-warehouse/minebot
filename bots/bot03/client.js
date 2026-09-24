const path = require("path");
const dotenv = require("dotenv");
const mineflayer = require("mineflayer");
const { MinecraftEnv, Transition, Decision } = require("./env");
const { TransitionWriter } = require("./recorder");


// --- Configs ---

// - env configs -

const env_path = path.resolve(__dirname, "..", ".env");
dotenv.config({ path: env_path });

let   NAME = process.env.BOTNAME;
const RANGE = Number.parseInt(process.env.RANGE, 10);
const HOST = process.env.HOST;
const PORT = 25565
const VERSION = process.env.MINECRAFT_VERSION;

// - initial setup -

const args = process.argv.slice(2);

let tick_counter = 0;
let running = false;
let slot = 0;
let policy = null;
let epLimit = -1;

for (const arg of args) {
  if (arg === "instant-run") {
    running = true;
    console.log('[INFO]: instant-run activated')
    continue;
  }

  const separatorIndex = arg.indexOf(":");

  if (separatorIndex === -1) {
    continue;
  }

  const key = arg.slice(0, separatorIndex);
  const value = arg.slice(separatorIndex + 1);

  if (key === "slot") {
    const parsedSlot = Number(value);

    if (!/^\d+$/.test(value) || !Number.isSafeInteger(parsedSlot)) {
      console.error("Enter a positive natural number!");
      process.exit(1);
    }

    slot = parsedSlot;
    NAME += slot
  }
  
  else if (key === "policy") {
    if (value.trim() === "") {
      console.error("Enter a positive natural number!");
      process.exit(1);
    }

    policy = value;
  }

  else if (key === "ep") {
    const parsedEP = Number(value)
    
    if (!/^\d+$/.test(value) || !Number.isSafeInteger(parsedEP)) {
      console.error("Enter a positive natural number!");
      process.exit(1);
    }

    epLimit = value;
  }
}

const environment = new MinecraftEnv(policy, epLimit);
const writer = new TransitionWriter();


// --- Essentials Connection things ---

const bot = mineflayer.createBot({
    username: NAME,
    host: HOST,
    port: PORT,
    version: VERSION,
    hideErrors: true
});

function login() {
    const bot_socket = bot._client.socket;
    console.log(
        `[INFO]: Logged in to ${bot_socket.server || bot_socket._host}`
    );
}

function kicked(reason, loggedIn) {
    if (loggedIn) {
        console.log(`[INFO]: Kicked from server: ${reason}`);
    } else {
        console.log(`[INFO]: Kicked whilst trying to connect: ${reason}`);
    }
}

function end(reason) {
    console.log(`[INFO]: Disconnected: ${reason}`);

    bot.removeListener("login", login);
    bot.removeListener("kicked", kicked);
    bot.removeListener("end", end);
}

function setSlot() {
    if (slot > 0) {
        bot.chat('/mv tp slot_' + slot);
    }
}

function spawn() {
    if (environment.limit_reached) {
        running = false;
        console.log("Episode Limit reached");
        bot.quit();
        return
    }
    bot.chat(`/tp ${NAME} 8.5 -60 8.5`)
}

bot.on("login", login);
bot.on('spawn', spawn);
bot.once('spawn', setSlot);
bot.on("kicked", kicked);
bot.on("end", end);

// --- Running and Death Managment ---

bot.on("death", () => {
    console.log(`[INFO]: Episode ${environment.episode} just finished!`);

    environment.on_death(get_state());
    write_transition(environment.pop_transitions());
});

bot.on("messagestr", (message, messagePosition) => {
    if (messagePosition !== "chat") {
        return;
    }

    const prefix = `bot ${NAME}`;
    const parts = message.split(" ");

    if (parts.length > 3 && parts[1] === "bot" && parts[2] === NAME) {
        const command = message.split(prefix, 2)[1].trim();

        if (command === "quit") {
            environment.on_death(get_state());
            write_transition(environment.pop_transitions());
            bot.quit();
        } else if (command === "run") {
            running = true;
            console.log("[INFO]: Turned on")
        } else if (command === "stop") {
            running = false;
            bot.clearControlStates();
            console.log("[INFO]: Turned off")
        } else {
            console.log(`${parts[0].slice(1, -1)} just said: ${command}`);
        }
    }
});


// --- Every tick trigger ---

function execute() {
    if (running) {
        const action = environment.on_tick(get_state());
        perform_action(action);
    }
}

bot.on("physicsTick", () => {
    tick_counter += 1;

    if (tick_counter >= environment.tick_every) {
        tick_counter = 0;
        execute();
    }
});


// --- Action ---

const MAX_PITCH = Math.PI / 2 - 0.01;

function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

function normalize_yaw(yaw) {
    return ((yaw + Math.PI) % (2 * Math.PI) + 2 * Math.PI) % (2 * Math.PI) - Math.PI;
}

function perform_action(action) {
    bot.clearControlStates();

    if ("controls" in action) {
        for (const control of action.controls) {
            bot.setControlState(control, true);
        }
    }

    if ("dyaw" in action || "dpitch" in action) {
        const new_yaw = normalize_yaw(bot.entity.yaw + (action.dyaw || 0));
        const new_pitch = clamp(
            bot.entity.pitch + (action.dpitch || 0),
            -MAX_PITCH,
            MAX_PITCH
        );
        bot.look(new_yaw, new_pitch);
    }

    if ("attack" in action) {
        const target = bot.entityAtCursor(RANGE);
        if (target) {
            bot.attack(target);
        } else {
            bot.swingArm("right");
        }
    }
}


// --- Game State Interpretation ---

function get_state() {
    const entity = bot.entity;
    const target = get_nearest_zombie();

    return {
        // bot state
        velocity: vector_to_tuple(entity.velocity),
        yaw: entity.yaw,
        pitch: entity.pitch,
        on_ground: entity.onGround,
        health: bot.health,

        // target
        target: target ? matrixAdition(target.position, bot.entity.position) : null,
    };
}

function vector_to_tuple(vector) {
    return [vector.x, vector.y, vector.z];
}

function get_nearest_zombie() {
    return bot.nearestEntity(entity => entity.name === 'zombie');
}


// --- Write transition ---

function write_transition(transitions) {
    writer.append(transitions);
}


// --- Utils ---

function matrixAdition(a, b) {
    return [a.x - b.x, a.y - b.y, a.z - b.z]
}


module.exports = { bot, environment, get_state, perform_action };