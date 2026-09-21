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
        const lines = transitions.map(t => JSON.stringify(t)).join("\n");
        fs.appendFileSync(this.file_path, lines + "\n");
    }
}

module.exports = { TransitionWriter };