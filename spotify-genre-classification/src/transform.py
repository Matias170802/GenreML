"""Transformación y validación del dataset de Spotify."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_PATH = PROCESSED_DIR / "spotify_audio_features.csv"

AUDIO_FEATURES = [
    "duration_ms",
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "time_signature",
]
TARGET = "track_genre"
UNIT_INTERVAL_FEATURES = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
]


def transform_data(raw_path: Path) -> Path:
    """Valida y selecciona las variables de audio del dataset raw."""
    raw_path = Path(raw_path)
    data = pd.read_csv(raw_path)

    print(f"Filas iniciales: {len(data)}")
    print(f"Columnas: {len(data.columns)}")
    print(f"Filas completamente duplicadas: {data.duplicated().sum()}")

    if "track_id" in data.columns:
        duplicated_track_ids = data["track_id"].duplicated().sum()
        print(f"track_id duplicados: {duplicated_track_ids}")
    else:
        print("track_id duplicados: no se pudo calcular (columna ausente)")

    print(f"Valores nulos: {data.isna().sum().sum()}")

    if "Unnamed: 0" in data.columns:
        data = data.drop(columns="Unnamed: 0")

    required_columns = AUDIO_FEATURES + [TARGET]
    missing_columns = [column for column in required_columns if column not in data.columns]
    if missing_columns:
        raise ValueError(
            "Faltan columnas requeridas en el dataset: " + ", ".join(missing_columns)
        )

    if data[TARGET].isna().any():
        raise ValueError("La columna track_genre contiene valores nulos.")

    for column in UNIT_INTERVAL_FEATURES:
        numeric_values = pd.to_numeric(data[column], errors="coerce")
        invalid_values = numeric_values.isna() | ~numeric_values.between(0, 1)
        if invalid_values.any():
            raise ValueError(
                f"La columna {column} contiene valores nulos, no numéricos "
                "o fuera del rango [0, 1]."
            )

    # Se excluyen artista, álbum y nombre de canción porque la pregunta
    # busca predecir el género únicamente a partir de características de audio.
    processed_data = data[required_columns].copy()

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    processed_data.to_csv(PROCESSED_PATH, index=False)

    print("Dataset procesado correctamente.")
    return PROCESSED_PATH
