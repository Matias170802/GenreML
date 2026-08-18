"""Extracción del dataset de Spotify desde Hugging Face."""

from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_PATH = RAW_DIR / "spotify_tracks.csv"
DATASET_URL = (
    "https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset/"
    "resolve/c4609440b24ac4075899f6e60b33775acbe00827/dataset.csv"
)


def extract_data() -> Path:
    """Descarga el dataset completo y devuelve la ruta del archivo raw."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = RAW_PATH.with_suffix(".csv.part")

    print("Descargando dataset completo...")

    try:
        with requests.get(DATASET_URL, stream=True, timeout=(10, 120)) as response:
            response.raise_for_status()
            with temporary_path.open("wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output_file.write(chunk)

        if temporary_path.stat().st_size == 0:
            raise ValueError("La descarga finalizó, pero el archivo recibido está vacío.")

        # Se conserva una copia completa del dataset original para mantener
        # trazabilidad y permitir reproducir las transformaciones desde cero.
        temporary_path.replace(RAW_PATH)
    except (requests.RequestException, OSError, ValueError) as error:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(
            "No se pudo descargar el dataset completo desde Hugging Face. "
            "Verificá la conexión a internet e intentá nuevamente."
        ) from error

    print("Dataset raw guardado correctamente.")
    return RAW_PATH
