const { loadModel, decide } = require('./policy')

const { TURN_STEP } = require('./configs/1/commands');

class Decision {
    constructor(state, action) {
        this.state = state;
        this.action = action;
    }
}

class Transition {
    constructor(state, action, nextState, done) {
        this.state = state;
        this.action = action;
        this.next_state = nextState;
        this.done = done;
    }
}


class MinecraftEnv {
    constructor(policy = null, epLimit = -1, tick_every = 2, config = 1) {
        this.COMMANDS = require(`./configs/${config}/commands`).COMMANDS;
        this.ACTIONS = Object.keys(this.COMMANDS);
        this.noop_action = this.ACTIONS.indexOf("noop");
        if (this.noop_action < 0) this.noop_action = 0;
        this.policy = policy ? loadModel('./pool/models/' + policy) : null;
        this.epLimit = epLimit != -1 ? epLimit : 1
        this.tick_every = tick_every;
        // decide once every X game ticks

        this.transitions = [];
        this._pending = null;
        this.episode = 1;
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
        
        let action = this.noop_action;
        if (state.target_in_range === true && this.policy != null) {
            action = decide(this.policy, state);
        }
        
        this._pending = new Decision(state, action);
        return this.COMMANDS[this.ACTIONS[action]];
    }

    end_episode(last_state = null) {
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
