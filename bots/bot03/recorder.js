const fs = require("fs");
const path = require("path");

class TransitionWriter {
    constructor(slot = 0) {
        if (slot == 0) slot = ""
        else slot = "_slot_" + String(slot)

        this.file_path = path.resolve(
            __dirname, "..", "..", "pool", "transitions", "transitions" + slot + ".jsonl"
        );
        
        fs.mkdirSync(path.dirname(this.file_path), { recursive: true });
    }

    append(transitions) {
        if (transitions.length === 0) {
            return;
        }

        let lines = ''

        for (let t=0; t<transitions.length; t++) {
            const transition = JSON.parse(JSON.stringify(transitions[t]))
            if (transition.state.target != null) {
                lines += JSON.stringify(transition) + '\n'
            }
        }

        fs.appendFileSync(this.file_path, lines);
    }
}

module.exports = { TransitionWriter };