## Training Instruction:

Create generation 0:

```sh
python -m src init --population 10 --config 1
```

Continue a generation 20 population through generation 24:

```sh
python -m src train --from-generation 20 --generations 4 --episodes 1 --config 1
```

Each population is stored under `pool/generations/gen-N`