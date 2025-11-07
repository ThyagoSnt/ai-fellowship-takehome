import argparse
import json
import time
import os
import yaml
from pathlib import Path
from modal_endpoint_app.src.pipeline.pipeline import Solution

def main(config_path: Path) -> None:
    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    json_path = Path(config["paths"]["json_path"])
    pdfs_root_path = Path(config["paths"]["pdfs_root_path"])

    solution = Solution()

    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    total_time = 0.0
    results_for_stats = []

    for idx, sample in enumerate(data):
        print(f"\nProcessing sample index: {idx}")
        label, extraction_schema, pdf_path = sample["label"], sample["extraction_schema"], sample["pdf_path"]
        start_time = time.perf_counter()
        solution.process_single_sample(idx, label, extraction_schema, os.path.join(pdfs_root_path, pdf_path))
        end_time = time.perf_counter()

        elapsed = end_time - start_time
        total_time += elapsed
        results_for_stats.append(elapsed)
        print(f"Sample {idx} processed in {elapsed:.2f} seconds")

    avg_time = total_time / len(results_for_stats) if results_for_stats else 0.0
    print("\n=== Processing Summary ===")
    print(f"Total samples: {len(results_for_stats)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average time per sample: {avg_time:.2f} seconds")

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run local parsing pipeline.")
    parser.add_argument(
        "-c", "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to YAML config file (default: config/config.yaml)",
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    main(config_path=args.config)
