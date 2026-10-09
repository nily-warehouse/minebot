from __future__ import annotations

from typing import Any

import neat

from .actions import ACTIONS_FILE, enabled_actions


INPUTS = [
    {"id": -1, "source": "velocity", "index": 0, "scale": 1.0},
    {"id": -2, "source": "velocity", "index": 1, "scale": 1.0},
    {"id": -3, "source": "velocity", "index": 2, "scale": 1.0},
    {"id": -4, "source": "yaw", "scale": 0.3183},
    {"id": -5, "source": "pitch", "scale": 0.6366},
    {"id": -6, "source": "on_ground", "scale": 1.0},
    {"id": -7, "source": "health", "scale": 0.05},
    {"id": -8, "source": "target", "index": 0, "scale": 0.1},
    {"id": -9, "source": "target", "index": 1, "scale": 0.1},
    {"id": -10, "source": "target", "index": 2, "scale": 0.1},
]

OUTPUTS = enabled_actions()


def load_config(
    path: str,
    population_size: int | None = None,
    outputs: list[str] | None = None,
    actions_file: str = str(ACTIONS_FILE),
) -> neat.Config:
    output_names = OUTPUTS if outputs is None else outputs
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        path,
    )

    genome_config = config.genome_config
    if genome_config.num_outputs != len(output_names):
        raise ValueError(
            f"{path} has num_outputs = {genome_config.num_outputs}, "
            f"but {actions_file} has {len(output_names)} enabled actions. "
            f"Set num_outputs = {len(output_names)} in {path}."
        )
    if genome_config.num_inputs != len(INPUTS):
        raise ValueError(
            f"{path} has num_inputs = {genome_config.num_inputs}, "
            f"but INPUTS has {len(INPUTS)} entries. "
            f"Set num_inputs = {len(INPUTS)} in {path}."
        )

    if population_size is not None:
        if population_size < 2:
            raise ValueError("population must contain at least two brains")
        config.pop_size = population_size
    config.action_names = list(output_names)
    return config


def _ordered_nodes(genome: neat.DefaultGenome) -> list[int]:
    indegree = {node_id: 0 for node_id in genome.nodes}
    outgoing: dict[int, list[int]] = {node_id: [] for node_id in genome.nodes}

    for connection in genome.connections.values():
        source, target = connection.key
        if not connection.enabled or source < 0:
            continue
        if source in genome.nodes and target in genome.nodes:
            indegree[target] += 1
            outgoing[source].append(target)

    ready = sorted(node_id for node_id, degree in indegree.items() if degree == 0)
    ordered: list[int] = []
    while ready:
        node_id = ready.pop(0)
        ordered.append(node_id)
        for target in outgoing[node_id]:
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
                ready.sort()

    if len(ordered) != len(genome.nodes):
        raise ValueError(f"genome {genome.key} is not feed forward")
    return ordered


def genome_to_model(
    genome: neat.DefaultGenome,
    config: neat.Config,
    generation: int,
) -> dict[str, Any]:
    output_ids = set(config.genome_config.output_keys)
    nodes = []
    for node_id in _ordered_nodes(genome):
        node = genome.nodes[node_id]
        if node.aggregation != "sum":
            raise ValueError("bot03 models support only sum aggregation")
        nodes.append(
            {
                "id": node_id,
                "type": "output" if node_id in output_ids else "hidden",
                "bias": node.bias,
                "response": node.response,
                "activation": node.activation,
            }
        )

    connections = [
        {
            "from": connection.key[0],
            "to": connection.key[1],
            "weight": connection.weight,
            "enabled": connection.enabled,
        }
        for connection in sorted(
            genome.connections.values(), key=lambda item: item.key
        )
    ]
    return {
        "format_version": 1,
        "generation": generation,
        "genome_id": genome.key,
        "inputs": INPUTS,
        "outputs": getattr(config, "action_names", OUTPUTS),
        "nodes": nodes,
        "connections": connections,
        "fitness": 0.0 if genome.fitness is None else genome.fitness,
    }