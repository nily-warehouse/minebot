## Training Instruction:

Create generation 0:

```sh
python -m src init --population 10
```

Continue a generation 20 population through generation 24:

```sh
python -m src train --from-generation 20 --generations 4 --episodes 1
```

Each population is stored under `pool/generations/gen-N`


## Note:
For changing actions consider these:
- `actions.json`
- `actions.py`
- `neat_config.ini` (the `num_outputs` parameter)
- `JS` side