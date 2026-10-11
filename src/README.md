## Training Instruction:

Create generation 0:

```sh
python -m src init --population 20 --config 1
```

Continue a generation 20 population through generation 24:

```sh
python -m src train --from-generation 0 --generations 5 --episodes 3 --config 1
```

Each population is stored under `pool/generations/gen-N`