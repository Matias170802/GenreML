"""Transformacion del dataset raw obtenido desde ReccoBeats."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from transform import AUDIO_FEATURES, PROCESSED_DIR, TARGET, UNIT_INTERVAL_FEATURES


PROCESSED_PATH = PROCESSED_DIR / "reccobeats_audio_features.csv"


def _to_processed_row(record: dict[str, Any]) -> dict[str, Any]:
    track = record.get("track") or {}
    features = record.get("audio_features") or {}

    row = {column: pd.NA for column in AUDIO_FEATURES + [TARGET]}
    row["duration_ms"] = track.get("durationMs")

    for column in AUDIO_FEATURES:
        if column in features:
            row[column] = features[column]

    # ReccoBeats no documenta genero de track; se mantiene la columna para
    # compatibilidad de esquema sin inventar etiquetas supervisadas.
    row[TARGET] = pd.NA
    return row


def transform_reccobeats_data(raw_path: Path) -> Path:
    """Convierte el JSON raw de ReccoBeats al esquema de audio features."""
    raw_path = Path(raw_path)
    with raw_path.open("r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    records = payload.get("records", [])
    if not records:
        raise ValueError("El archivo raw de ReccoBeats no contiene registros.")

    processed_data = pd.DataFrame(_to_processed_row(record) for record in records)
    required_columns = AUDIO_FEATURES + [TARGET]
    processed_data = processed_data.reindex(columns=required_columns)

    before_duplicates = len(processed_data)
    processed_data = processed_data.drop_duplicates().reset_index(drop=True)

    print(f"Filas iniciales ReccoBeats: {len(records)}")
    print(f"Filas duplicadas removidas: {before_duplicates - len(processed_data)}")
    print(f"Columnas procesadas: {len(processed_data.columns)}")

    for column in AUDIO_FEATURES:
        processed_data[column] = pd.to_numeric(processed_data[column], errors="coerce")

    missing_audio_values = processed_data[AUDIO_FEATURES].isna().sum()
    missing_columns = [
        column for column, missing in missing_audio_values.items() if missing == len(processed_data)
    ]
    if missing_columns:
        print(
            "Columnas sin datos en ReccoBeats preservadas por compatibilidad: "
            + ", ".join(missing_columns)
        )

    for column in UNIT_INTERVAL_FEATURES:
        numeric_values = processed_data[column]
        invalid_values = numeric_values.notna() & ~numeric_values.between(0, 1)
        if invalid_values.any():
            raise ValueError(f"La columna {column} contiene valores fuera del rango [0, 1].")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    try:
        processed_data.to_csv(PROCESSED_PATH, index=False)
    except PermissionError as error:
        raise PermissionError(
            f"No se pudo escribir {PROCESSED_PATH}. "
            "Cerrá el archivo si está abierto en Excel u otro programa e intentá nuevamente."
        ) from error

    print(f"Dataset ReccoBeats procesado correctamente: {PROCESSED_PATH}")
    return PROCESSED_PATH
