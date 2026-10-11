const TURN_STEP = Math.PI / 12;

const COMMANDS = {
    "noop":
        {},
    "forward":
        { "controls": ["forward"] },
    "back":
        { "controls": ["back"] },
    "turn_left":
        { "dyaw": TURN_STEP },
    "turn_right":
        { "dyaw": -TURN_STEP },
};

module.exports = { COMMANDS, TURN_STEP };