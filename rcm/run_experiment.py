"""Solving trains QUBO using D-Wave."""
import argparse
import json
import logging
import pickle
from itertools import product
from pathlib import Path
from typing import List

import pydantic
import yaml
from dimod import BinaryQuadraticModel, Sampler
from dimod.sampleset import SampleSet, concatenate
from dimod.serialization import coo
from dimodmock import StructuredMock
from dwave.embedding import embed_bqm, unembed_sampleset
from dwave.system import DWaveSampler
from tqdm import tqdm

RAW_RESULT_FILE_PATTERN = "output_raw_part_{batch_num}_at_{at}_css_{css}.json"
UNEMBEDDED_RESULT_FILE_PATTERN = "output_at_{at}_css_{css}.csv"

logger = logging.getLogger("__name__")


class ConfigModel(pydantic.BaseModel):
    """Representation of configuration file for an experiment."""
    solver_name: str  # Name of the D-Wave solver to use
    input_file: str  # Input QUBO
    embedding_file: str  # Path to pickled embedding (has to be found be external script)
    output_dir: str  # Output directory
    chain_strength_scales: List[float]  # List of chain strength scales to use
    annealing_times: List[int]  # List of annealing times to use
    batch_size: int  # Number of reads in a batch (i.e. a single run)
    num_batches: int  # Number of batches (i.e. number of runs)


def find_energy_scale(bqm: BinaryQuadraticModel):
    """Find smallest and largest (wrt absolute value) interaction in given BQM."""
    absolute_interactions = [
        abs(coeff) for coeff in bqm.quadratic.values() if coeff != 0
    ]
    return min(absolute_interactions), max(absolute_interactions)


def sample_or_load(
    sampler: Sampler,
    embedded_bqm: BinaryQuadraticModel,
    css: float,
    annealing_time: int,
    batch_num: int,
    batch_size: int,
    output_path
):
    """Sample from a given BQM or load previously computed result if it's already saved."""
    if output_path.exists():
        logger.info(
            "Skipping batch %s @ css=%f and at=%d because its already computed.",
            batch_num,
            css,
            annealing_time,
        )
        with open(output_path) as output_file:
            sample_set = SampleSet.from_serializable(json.load(output_file))
    else:
        sample_set = sampler.sample(
            embedded_bqm,
            annealing_time=annealing_time,
            num_reads=batch_size,
            answer_mode="raw",
        )

        with open(output_path, "w") as output_file:
            json.dump(sample_set.to_serializable(), output_file)

    return sample_set


def run_experiment(config: ConfigModel, mock: bool):
    """Run experiment described by given config, possibly mocking-out the real sampler."""
    with open(config.embedding_file, "rb") as embedding_file:
        embedding = pickle.load(embedding_file)

    with open(config.input_file) as bqm_file:
        bqm = coo.load(bqm_file, vartype="BINARY")

    _, max_en = find_energy_scale(bqm)

    sampler = DWaveSampler(solver=config.solver_name)

    if mock:
        sampler = StructuredMock.from_sampler(sampler)

    parameter_range = tqdm(
        list(product(config.chain_strength_scales, config.annealing_times))
    )

    root = Path(config.output_dir)
    try:
        root.mkdir()
        root.joinpath("raw_outputs").mkdir()
        root.joinpath("outputs").mkdir()
    except OSError:
        logger.warning("Experiment directory already exists.")

    for css, at in parameter_range:
        emb_bqm = embed_bqm(
            source_bqm=bqm,
            embedding=embedding,
            target_adjacency=sampler.adjacency,
            chain_strength=0.5 * css * max_en,
        )
        sample_sets = []
        for batch_num in range(config.num_batches):
            output_path = (
                root / "raw_outputs" /
                RAW_RESULT_FILE_PATTERN.format(css=css, at=at, batch_num=batch_num)
            )
            sample_set = sample_or_load(
                sampler,
                embedded_bqm=emb_bqm,
                css=css,
                annealing_time=at,
                batch_num=batch_num,
                batch_size=config.batch_size,
                output_path=output_path
            )

            sample_sets.append(sample_set)

        total_sampleset = concatenate(sample_sets)
        unembedded_results = unembed_sampleset(total_sampleset, embedding, bqm)
        unembedded_results.to_pandas_dataframe().to_csv(
            root / "outputs" / UNEMBEDDED_RESULT_FILE_PATTERN.format(css=css, at=at),
            index=False,
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Sample railway conflict management QUBO, optionally using mock simulator."
    )
    parser.add_argument("config", help="Configuration file.")
    parser.add_argument(
        "--mock",
        help=(
            "Use mock simulator instead of real machine. Warning: this will return random "
            "results without using your time on D-Wave."
        ),
        action="store_true",
    )
    return parser.parse_args()


def main():
    """Entrypoint of this script."""
    args = parse_args()

    logging.basicConfig(level="INFO")

    with open(args.config) as config_file:
        config = ConfigModel(**yaml.safe_load(config_file))

    run_experiment(config, args.mock)


if __name__ == "__main__":
    main()
