const path = require("path");
const fs = require("fs");
const dotenv = require("dotenv");
const mineflayer = require("mineflayer");
const { MinecraftEnv } = require("./env");
const { TransitionWriter } = require("./recorder");


// --- Configs ---

// - env configs -

const env_path = path.resolve(__dirname, ".env");
dotenv.config({ path: env_path });

let   NAME = process.env.BOTNAME;
const HOST = process.env.HOST;
const PORT = 25565
const VERSION = process.env.MINECRAFT_VERSION;
const ITEM_TARGET_RANGE = Number.parseFloat(process.env.RANGE);
const VERBOSE = /^(1|true|yes|on)$/i.test(process.env.VERBOSE || "");
const EPISODE_TIMEOUT_SECONDS = Number(process.env.EPISODE_TIMEOUT_SECONDS);

const EPISODE_TIMEOUT_MS = EPISODE_TIMEOUT_SECONDS * 1000;

let teleporting = false;
let tp_ticks = 0;
const TP_TIMEOUT_TICKS = 40;

// - initial setup -

const args = process.argv.slice(2);

let tick_counter = 0;
let running = false;
let slot = 0;
let policy = null;
let epLimit = -1;
let config = 1;
let episode_timer = null;
let current_target_id = null;
let current_target_completed = false;
let no_target_logged = false;

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
      console.error("Slot must be a non-negative integer!");
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

  else if (key === "config") {
    const parsedConfig = Number(value);

    if (!/^\d+$/.test(value) || !Number.isSafeInteger(parsedConfig) || parsedConfig < 1) {
      console.error("Config must be a positive integer!");
      process.exit(1);
    }

    config = parsedConfig;
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

function loadArena(slotNumber) {
  const arenaConfigPath = path.resolve(__dirname, "configs", "arenas.json");
  let arenas;

  try {
    arenas = JSON.parse(fs.readFileSync(arenaConfigPath, "utf8"));
  } catch (error) {
    console.error(`[ERROR]: Could not load ${arenaConfigPath}: ${error.message}`);
    process.exit(1);
  }

  if (arenas === null || typeof arenas !== "object" || Array.isArray(arenas)) {
    console.error(`[ERROR]: ${arenaConfigPath} must contain an object keyed by slot.`);
    process.exit(1);
  }

  const arena = arenas[String(slotNumber)];
  if (!arena) {
    console.error(
      `[ERROR]: No arena is configured for slot ${slotNumber} in ${arenaConfigPath}`
    );
    process.exit(1);
  }

  const values = [
    arena.center?.x,
    arena.center?.y,
    arena.center?.z,
    arena.corners?.lower?.x,
    arena.corners?.lower?.z,
    arena.corners?.upper?.x,
    arena.corners?.upper?.z,
  ];
  if (!values.every(Number.isFinite)) {
    console.error(
      `[ERROR]: Arena slot ${slotNumber} must define numeric center coordinates ` +
      "and lower/upper corner x/z coordinates."
    );
    process.exit(1);
  }

  if (arena.corners.lower.x >= arena.corners.upper.x ||
      arena.corners.lower.z >= arena.corners.upper.z) {
    console.error(`[ERROR]: Arena slot ${slotNumber} has invalid corner bounds.`);
    process.exit(1);
  }

  return {
    centerX: arena.center.x,
    centerY: arena.center.y,
    centerZ: arena.center.z,
    lowerBoundX: arena.corners.lower.x,
    upperBoundX: arena.corners.upper.x,
    lowerBoundZ: arena.corners.lower.z,
    upperBoundZ: arena.corners.upper.z,
  };
}

const {
  centerX,
  centerY,
  centerZ,
  lowerBoundX,
  upperBoundX,
  lowerBoundZ,
  upperBoundZ,
} = loadArena(slot);

const environment = new MinecraftEnv(policy, epLimit, 2, config);
const writer = new TransitionWriter(slot);


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
    clear_episode_timer();
    console.log(`[INFO]: Disconnected: ${reason}`);

    bot.removeListener("login", login);
    bot.removeListener("kicked", kicked);
    bot.removeListener("end", end);
}

function spawn() {
    current_target_id = null;
    current_target_completed = false;
    no_target_logged = false;
    clear_episode_timer();

    if (environment.limit_reached) {
        running = false;
        console.log("Episode Limit reached");
        bot.quit();
        return
    }

    teleporting = true;
    send_tp();
}


// initial teleport

function near_arena_center() {
    const p = bot.entity.position;
    return Math.abs(p.x - centerX) < 0.5 &&
        Math.abs(p.y - centerY) < 0.5 &&
        Math.abs(p.z - centerZ) < 0.5;
}

function send_tp() {
    bot.clearControlStates();
    bot.chat(`/tp ${NAME} ${centerX} ${centerY} ${centerZ}`);
    tp_ticks = 0;
}

function clear_episode_timer() {
    if (episode_timer !== null) {
        clearTimeout(episode_timer);
        episode_timer = null;
    }
}

function start_episode_timer() {
    clear_episode_timer();
    episode_timer = setTimeout(() => {
        episode_timer = null;
        console.log(
            `[INFO]: Episode ${environment.episode} reached the ` +
            `${EPISODE_TIMEOUT_SECONDS}s timeout`
        );
        bot.chat(`/kill ${NAME}`);
    }, EPISODE_TIMEOUT_MS);
}

bot.on("login", login);
bot.on('spawn', spawn);
bot.on("kicked", kicked);
bot.on("end", end);

bot.on("playerCollect", (collector, collected) => {
    if (collector?.id !== bot.entity?.id || collected?.id !== current_target_id ||
        current_target_completed) {
        return;
    }

    current_target_completed = true;
    log_target(
        `Target achieved: dropped item ${current_target_id} was collected by the bot.`
    );

    bot.chat(`/tp ${NAME} ${centerX} ${centerY} ${centerZ}`);
});

// --- Running and Death Managment ---

bot.on("death", () => {
    clear_episode_timer();
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
        checkArena();
    }
}

bot.on("physicsTick", () => {
    if (teleporting) {
        if (near_arena_center()) {
            teleporting = false;
            start_episode_timer();
        } else if (++tp_ticks >= TP_TIMEOUT_TICKS) {
            send_tp();
        }
        return;
    }

    tick_counter += 1;

    if (tick_counter >= environment.tick_every) {
        tick_counter = 0;
        execute();
    }
});


// --- Arena border magnagement ---

function checkArena() {
    boundCheck = (
        bot.entity.position.x < lowerBoundX ||
        bot.entity.position.x > upperBoundX ||
        bot.entity.position.z < lowerBoundZ ||
        bot.entity.position.z > upperBoundZ
    )

    if (boundCheck){
        bot.chat(`/tp ${NAME} ${centerX} ${centerY} ${centerZ}`);
    }
}

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
}


// --- Game State Interpretation ---

function get_state() {
    const entity = bot.entity;
    const target = get_current_target();
    const offset = target ? matrixAdition(target.position, entity.position) : null;
    const target_distance = target ? distance_between(entity.position, target.position) : null;
    const target_in_range = target_distance !== null &&
        target_distance <= ITEM_TARGET_RANGE && !current_target_completed;

    const yaw = entity.yaw;
    // target offset in the bot's own frame (yaw 0 faces -z, turn_left = +yaw)
    const target_forward = offset ? -offset[0] * Math.sin(yaw) - offset[2] * Math.cos(yaw) : null;
    const target_right   = offset ?  offset[0] * Math.cos(yaw) - offset[2] * Math.sin(yaw) : null;

    return {
        // bot
        velocity: vector_to_tuple(entity.velocity),
        yaw: entity.yaw,

        // target
        target_id: target ? target.id : null,
        target_distance,
        target_in_range,
        target_forward,
        target_right,
    };
}

function vector_to_tuple(vector) {
    return [vector.x, vector.y, vector.z];
}

function get_current_target() {
    if (current_target_id !== null) {
        const target = bot.entities[current_target_id];
        if (target?.name === "item" && target.position != null) {
            return target;
        }

        if (!current_target_completed) {
            log_target(`Target lost: dropped item ${current_target_id} disappeared.`);
        }
        current_target_id = null;
        current_target_completed = false;
    }

    const candidate = bot.nearestEntity(e => {
        if (e.name !== "item" || e.position == null) return false;
        return distance_between(bot.entity.position, e.position) <= ITEM_TARGET_RANGE;
    });

    if (!candidate) {
        if (!no_target_logged) {
            log_target(`No dropped item within RANGE=${ITEM_TARGET_RANGE} blocks.`);
            no_target_logged = true;
        }
        return null;
    }

    current_target_id = candidate.id;
    current_target_completed = false;
    no_target_logged = false;
    log_target(
        `Detected dropped item ${candidate.id} at ` +
        `${distance_between(bot.entity.position, candidate.position).toFixed(2)} blocks.`
    );
    return candidate;
}

function log_target(message) {
    if (VERBOSE) {
        console.log(`[TARGET] ${message}`);
    }
}


// --- Write transition ---

function write_transition(transitions) {
    writer.append(transitions);
}


// --- Utils ---

function matrixAdition(a, b) {
    return [a.x - b.x, a.y - b.y, a.z - b.z]
}

function distance_between(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    const dz = a.z - b.z;
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
}


module.exports = { bot, environment, get_state, perform_action };
