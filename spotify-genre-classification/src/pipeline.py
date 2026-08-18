"""Orquestador del pipeline ETL de Spotify Genre Classification."""

from extract import extract_data
from transform import transform_data


def run_pipeline() -> None:
    """Ejecuta secuencialmente las etapas de extracción y transformación."""
    print("Spotify Genre Classification - ETL Pipeline\n")

    print("[1/2] Extracción")
    raw_path = extract_data()

    print("\n[2/2] Transformación")
    processed_path = transform_data(raw_path)

    print("\nPipeline finalizado correctamente.")
    print(f"Dataset procesado: {processed_path.relative_to(processed_path.parents[2])}")


if __name__ == "__main__":
    run_pipeline()
