"""Orquestador del pipeline ETL alternativo con ReccoBeats."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from reccobeats_extract import DEFAULT_TARGET_TRACKS, extract_reccobeats_data
from reccobeats_transform import transform_reccobeats_data


def run_reccobeats_pipeline(target_tracks: int = DEFAULT_TARGET_TRACKS) -> None:
    """Ejecuta secuencialmente extraccion y transformacion de ReccoBeats."""
    print("Spotify Genre Classification - ReccoBeats ETL Pipeline\n")

    print("[1/2] Extraccion ReccoBeats")
    raw_path = extract_reccobeats_data(target_tracks=target_tracks)

    print("\n[2/2] Transformacion ReccoBeats")
    processed_path = transform_reccobeats_data(raw_path)

    print("\nPipeline ReccoBeats finalizado correctamente.")
    print(f"Dataset raw: {raw_path.relative_to(raw_path.parents[2])}")
    print(f"Dataset procesado: {processed_path.relative_to(processed_path.parents[2])}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipeline ETL alternativo con ReccoBeats.")
    parser.add_argument(
        "--target-tracks",
        type=int,
        default=DEFAULT_TARGET_TRACKS,
        help="Cantidad aproximada de canciones unicas a obtener.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_reccobeats_pipeline(target_tracks=args.target_tracks)
