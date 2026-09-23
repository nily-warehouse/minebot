const fs = require("fs");
const path = require("path");

const TRANSITIONS_FILE = path.resolve(
    __dirname, "..", "..", "pool", "transitions", "transitions.jsonl"
);

class TransitionWriter {
    constructor(file_path = TRANSITIONS_FILE) {
        this.file_path = file_path;
        fs.mkdirSync(path.dirname(file_path), { recursive: true });
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