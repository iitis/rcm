# RCM Railway Conflict Management using D-Wave

This repository contains code used for running experiments in the
paper 

Krzysztof Domino, Mátyás Koniorczyk, Krzysztof Krawiec, Konrad Jałowiecki, Sebastian Deffner, Bartłomiej Gardas
*[Quantum annealing in the NISQ era: railway conflict management](https://arxiv.org/abs/2112.03674)*

## About

This repository provides `rcm` (short for Railway Conflict Management) Python package. The 
package contains scripts that cen be used for reproducing results from the manuscript:

- `rcm-find-min-chimera-size`: script for (heuristically) determining minimum lattice size of 
  a square Chimera graph on which given Binary Quadratic Model can be embedded.
- `rcm-run-experiment`: script for running actual experiments on D-Wave annealers.

## Installation

We highly recommend using fresh virtual environment or conda environment for the package
installation. Note that repository is compatible with Python >= 3.8.

1. Clone or download the repository.
2. In the root directory of the repository run
   ```bash
   pip install .
   ```
   This will install all the dependencies as well as the `rcm` package. Command line scripts 
   will be installed and can be invoked directly from the shell as long as the correct virtual 
   environment is active.

## Command line interface

The package provides several command line utilities.

### rcm-run-experiment

This script is used to run actual experiments on D-Wave. Optionally, experiments could be run with
mock simulator
(using the [dimodmock](https://pypi.org/project/dimodmock/) package)
instead, which can be useful for checking integration with the rest of your pipeline before 
running actual experiments on D-Wave.

```text
usage: rcm-run-experiment [-h] [--mock] config

Sample railway conflict management QUBO, optionally using mock simulator.

positional arguments:
  config      Configuration file.

optional arguments:
  -h, --help  show this help message and exit
  --mock      Use mock simulator instead of real machine. Warning: this will return random results without using your time on D-Wave.
```

The configuration file describes the experiment. An example below (as well as
the `example-config.yaml` file)
shows the expected file format. Please refer to the manuscript for the explanation of the 
terminology
used in comments.

Experiments are run in *batches*, since D-Wave API has a limit on a single job duration. For
instance, you might wish to split your experiment comprising 10k reads into 10 batches of 1k reads.

All experiments run by this script are checkpointed, meaning that running the same experiment with
the same, unchanged configuration file will reuse any previous partial result. This is useful e.g.
in case of a network failure. If you wish to perform a fresh experiment, you have to manually remove
the output directory.

```yaml
solver_name: DW_2000Q_6             # Name of the D-Wave solver to use
input_file: qubo.txt                # Path (relative or absolute) to the instance file
embedding_file: embedding.pickle    # Path to the embedding saved as pickle file
# Embeddings should be saved as 
output_dir: ./result                # Path (relative or absolute) where results should be saved
chain_strength_scales: [ 2.0, 3.0 ] # List of chain strength scales to use
annealing_times: [ 5, 20 ]          # List of annealing time (in microseconds) to use
batch_size: 100                     # Batch size
num_batches: 2                      # Number of batches
```

### rcm-find-min-chimera-size

This script is used for finding minimum size of a square Chimera graph for which given problem can
embedded. Note that this is merely a convenience script for using
[minorminer](https://github.com/dwavesystems/minorminer).

```text
usage: rcm-find-min-chimera-size [-h] [--num-tries NUM_TRIES] [--min-size MIN_SIZE] [--max-size MAX_SIZE] [--threads THREADS] [--seed SEED] instance

Find minimum size (number of rows and columns) of a square Chimera lattice for which given 
problem can be embedded.

positional arguments:
  instance

optional arguments:
  -h, --help            show this help message and exit
  --num-tries NUM_TRIES
                        Number of tries for minorminer runs
  --min-size MIN_SIZE   Smallest square Chimera size to try.
  --max-size MAX_SIZE   Largest square Chimera size to try. If not provided, larger Chimera sizes will be tried until an embedding is found.
  --threads THREADS     Number of threads to use by minorminer.
  --seed SEED           Random seed passed to minorminer
```
