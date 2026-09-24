const fs = require("fs");

// activation defenition
const clamp = x => Math.max(-60, Math.min(60, x));
const ACT = {
  tanh: x => Math.tanh(clamp(2.5 * x)),
  sigmoid: x => 1 / (1 + Math.exp(-clamp(5 * x))),
  relu: x => (x > 0 ? x : 0),
};

const loadModel = (path) => { 
    m = JSON.parse(fs.readFileSync(path, "utf8"))
    console.log('[INFO]: Model loaded successfuly')
    return m;
};

function encode(model, state) {
  return model.inputs.map(s => {
    let v = state[s.source];
    if (s.index !== undefined) v = v[s.index];
    return Number(v) * s.scale;
  });
}

function decide(model, state) {
  const values = {};
  encode(model, state).forEach((x, i) => { values[model.inputs[i].id] = x; });

  for (const node of model.nodes) {
    let sum = 0;
    for (const c of model.connections)
      if (c.enabled && c.to === node.id) sum += values[c.from] * c.weight;
    values[node.id] = ACT[node.activation](node.bias + node.response * sum);
  }

  const out = model.outputs.map((_, i) => values[i]);
  return out.indexOf(Math.max(...out));
}

module.exports = { loadModel, decide };