import logging
from pathlib import Path

import pandas as pd
import yaml

from patterns.compile_normalization_patterns import build_normalization_pattern
from patterns.compile_frequency_patterns import build_frequency_pattern
from pipeline import run_pipeline


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


def main():

    # Config
    with open("config.yaml") as f:
        cfg = yaml.safe_load(f)

    dataset_name = cfg["active_dataset"]
    ds = cfg["datasets"][dataset_name]

    raw_med_col = ds.get(
        "raw_med_col_override",
        f"{ds['col_str_name']}simulated",
    )

    # Paths
    root = Path(__file__).resolve().parent.parent

    data_dir = root / "data"
    rxnorm_dir = data_dir / "RxNorm_full_05042026" / "rrf"

    norm_path = data_dir / "normalization_dictionary.csv"
    freq_path = data_dir / "frequency_dictionary.csv"

    rxnorm_rrf_path = rxnorm_dir / "RXNCONSO.RRF"
    rxnrel_rrf_path = rxnorm_dir / "RXNREL.RRF"

    # Load data
    logger.info("Loading %s", dataset_name)

    df = pd.read_csv(data_dir / ds["file"])
    df = df[ds["cols"]]

    # Compile patterns
    logger.info("Compiling patterns")

    compiled_norm_patterns = build_normalization_pattern(
        path=norm_path
    )

    compiled_freq_patterns = build_frequency_pattern(
        path=freq_path
    )

    # Run pipeline
    logger.info("Running pipeline")

    df = run_pipeline(
        df=df,
        raw_med_col=raw_med_col,
        compiled_norm_patterns=compiled_norm_patterns,
        compiled_freq_patterns=compiled_freq_patterns,
        rxnorm_rrf_path=rxnorm_rrf_path,
        rxnrel_rrf_path=rxnrel_rrf_path,
    )

    # Save output
    output_path = (
        data_dir
        / dataset_name
        / "output"
        / f"out_{dataset_name}.csv"
    )

    logger.info("Saving output")

    df.to_csv(output_path, index=False)

    logger.info("Done")


if __name__ == "__main__":
    main()