const { loadModel, decide } = require('./policy')

const TURN_STEP = Math.PI / 12;

class Decision {
    constructor(state, action) {
        this.state = state;
        this.action = action;
    }
}

class Transition {
    constructor(state, action, reward, nextState, done) {
        this.state = state;
        this.action = action;
        this.next_state = nextState;
        this.done = done;
    }
}


class MinecraftEnv {
    static COMMANDS = {
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
    static ACTIONS = Object.keys(MinecraftEnv.COMMANDS);

    constructor(policy = null, epLimit = -1, tick_every = 2) {
        this.policy = policy ? loadModel('./pool/models/' + policy) : null;
        this.epLimit = epLimit != -1 ? epLimit : 1
        this.tick_every = tick_every;
        // decide once every X game ticks

        this.transitions = [];
        this._pending = null;
        this.episode = 1;
    }

    get COMMANDS() {
        return MinecraftEnv.COMMANDS;
    }

    get ACTIONS() {
        return MinecraftEnv.ACTIONS;
    }

    get n_actions() {
        return this.ACTIONS.length;
    }

    get limit_reached() {
        return this.episode > this.epLimit;
    }


    // --- steps ---

    on_tick(state) {
        this._finish_pending_step(state, false);
        
        let action = 0
        if (state.target != null && this.policy != null) {
            action = decide(this.policy, state);
        }
        
        this._pending = new Decision(state, action);
        return this.COMMANDS[this.ACTIONS[action]];
    }

    on_death(last_state = null) {
        this.episode += 1;
        if (this._pending === null) {
            return;
        }
        const final_state = last_state || this._pending.state;
        this._finish_pending_step(final_state, true);
    }

    pop_transitions() {
        const finished = this.transitions;
        this.transitions = [];
        return finished;
    }

    _finish_pending_step(next_state, done) {
        if (this._pending === null) {
            return;
        }
        const { state, action } = this._pending;
        this.transitions.push(new Transition(state, action, next_state, done));
        this._pending = null;
    }
}

module.exports = { MinecraftEnv, Decision, Transition, TURN_STEP };