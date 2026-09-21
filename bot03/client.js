const path = require("path");
const dotenv = require("dotenv");
const mineflayer = require("mineflayer");
const { MinecraftEnv } = require("./env");


// --- Configs ---

let running = false;

const env_path = path.resolve(__dirname, "..", ".env");
dotenv.config({ path: env_path });

const NAME = process.env.BOTNAME;
const RANGE = Number.parseInt(process.env.RANGE, 10);
const HOST = process.env.HOST;
const PORT = 25565
const VERSION = process.env.MINECRAFT_VERSION;


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

bot.on("login", login);
bot.on("kicked", kicked);
bot.on("end", end);


// --- Main Area ---

const environment = new MinecraftEnv(null, null, RANGE);

function execute() {
    if (running) {
        const action = environment.on_tick(get_state());
        perform_action(action);
    }
}

let tick_counter = 0;

bot.on("death", () => {
    console.log(`[INFO]: Episode ${environment.episode} just finished!`);

    environment.on_death(get_state());

    if (environment.limit_reached) {
        running = false;
        console.log("Episode Limit reached");
        bot.quit();
    }
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

bot.on("physicsTick", () => {
    tick_counter += 1;

    if (tick_counter >= environment.tick_every) {
        tick_counter = 0;
        execute();
    }
});

function perform_action(action) {
    bot.clearControlStates();

    // move
    if ("controls" in action) {
        for (const control of action.controls) {
            bot.setControlState(control, true);
        }
    }

    // look around
    if ("dyaw" in action || "dpitch" in action) {
        bot.look(
            bot.entity.yaw + (action.dyaw || 0),
            bot.entity.pitch + (action.dpitch || 0),
        );
    }

    // attack
    if ("attack" in action) {
        const target = bot.entityAtCursor(RANGE);
        if (target) {
            bot.attack(target);
        } else {
            bot.swingArm("right");
        }
    }
}


const UNKNOWN_BLOCK = "unknown";

function get_state() {
    const entity = bot.entity;
    return {
        position: vector_to_tuple(entity.position),
        velocity: vector_to_tuple(entity.velocity),
        yaw: entity.yaw,
        pitch: entity.pitch,
        on_ground: entity.onGround,
        health: bot.health,
        food: bot.food,
        blocks: get_block_grid(environment.grid_radius),
    };
}

function vector_to_tuple(vector) {
    return [vector.x, vector.y, vector.z];
}

function get_block_grid(radius) {
    const center = bot.entity.position.floored();
    const offsets = Array.from({ length: 2 * radius + 1 }, (_, index) => index - radius);
    return offsets.map(dx =>
        offsets.map(dy =>
            offsets.map(dz => get_block_name(center.offset(dx, dy, dz)))
        )
    );
}

function get_block_name(position) {
    const block = bot.blockAt(position);
    return block ? block.name : UNKNOWN_BLOCK;
}

module.exports = { bot, environment, get_state, perform_action };