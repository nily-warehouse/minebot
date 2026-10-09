const TURN_STEP = Math.PI / 12;

const COMMANDS = {
    "noop":
        {},
    "forward":
        { "controls": ["forward"] },
    "back":
        { "controls": ["back"] },
    "left":
        { "controls": ["left"] },
    "right":
        { "controls": ["right"] },
    "jump":
        { "controls": ["jump"] },
    "sprint_forward":
        { "controls": ["forward", "sprint"] },
    "turn_left":
        { "dyaw": TURN_STEP },
    "turn_right":
        { "dyaw": -TURN_STEP },
    "look_up":
        { "dpitch": TURN_STEP },
    "look_down":
        { "dpitch": -TURN_STEP },
    "attack":
        { "attack": true },
};

module.exports = { COMMANDS, TURN_STEP };