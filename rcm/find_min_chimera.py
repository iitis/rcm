import argparse
import logging

import dimod
import dimod.serialization.coo as coo
import minorminer
from dwave_networkx import chimera_graph


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Find minimum size (number of rows and columns) of a square Chimera lattice for which "
            "given problem can be embedded."
        )
    )
    parser.add_argument("instance", type=argparse.FileType("r"))
    parser.add_argument(
        "--num-tries", type=int, default=10, help="Number of tries for minorminer runs"
    )
    parser.add_argument(
        "--min-size", type=int, default=16, help="Smallest square Chimera size to try."
    )
    parser.add_argument(
        "--max-size",
        type=int,
        help=(
            "Largest square Chimera size to try. If not provided, larger Chimera sizes will be "
            "tried until an embedding is found."
        ),
    )
    parser.add_argument(
        "--threads", type=int, help="Number of threads to use by minorminer.", default=1
    )
    parser.add_argument(
        "--seed", type=int, help="Random seed passed to minorminer", default=None
    )
    return parser.parse_args()


def main():
    """Entrypoint of this script."""
    args = parse_args()

    bqm_graph = dimod.to_networkx_graph(coo.load(args.instance, vartype="BINARY"))

    size = args.min_size
    max_size = float("inf") if args.max_size is None else args.max_size
    if max_size < size:
        raise ValueError("Invalid arguments (min-size > max_size)")

    found = False
    embedding = None

    logger = logging.getLogger(__name__)
    logging.basicConfig(level="INFO")

    while size <= max_size and not found:
        logger.info("Trying Chimera size: %d", size)
        solver_graph = chimera_graph(size, size)

        embedding = minorminer.find_embedding(
            bqm_graph,
            solver_graph,
            tries=args.num_tries,
            random_seed=args.seed,
            threads=args.threads,
        )

        if embedding:
            found = True
        else:
            size += 1

    if embedding is None:
        raise ValueError("No embedding could be found.")
    else:
        print(size)


if __name__ == "__main__":
    main()
