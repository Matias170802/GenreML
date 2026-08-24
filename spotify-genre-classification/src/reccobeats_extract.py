"""Extraccion de tracks y audio features desde ReccoBeats."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_PATH = RAW_DIR / "reccobeats_tracks_raw.json"

BASE_URL = "https://api.reccobeats.com/v1"
REQUEST_TIMEOUT = (10, 60)
DEFAULT_TARGET_TRACKS = 500
SEARCH_PAGE_SIZE = 50
REQUEST_PAUSE_SECONDS = 0.35

# Terminos amplios y reproducibles para cubrir distintos estilos sin depender
# de pasos manuales ni credenciales externas.
DEFAULT_SEARCH_TERMS = [
    "rock",
    "pop",
    "jazz",
    "classical",
    "hip hop",
    "electronic",
    "country",
    "latin",
    "reggae",
    "metal",
]


def _request_json(
    session: requests.Session,
    endpoint: str,
    *,
    params: dict[str, Any] | None = None,
    max_attempts: int = 4,
) -> Any:
    """Ejecuta un GET y respeta Retry-After cuando la API limita requests."""
    url = f"{BASE_URL}{endpoint}"

    for attempt in range(1, max_attempts + 1):
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)

        if response.status_code == 429 and attempt < max_attempts:
            retry_after = response.headers.get("Retry-After")
            wait_seconds = float(retry_after) if retry_after else attempt * 2.0
            time.sleep(wait_seconds)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError(f"No se pudo obtener respuesta valida desde {url}.")


def _content(payload: Any) -> list[dict[str, Any]]:
    """Normaliza respuestas que pueden venir como lista o como {'content': [...]}."""
    if isinstance(payload, dict) and isinstance(payload.get("content"), list):
        return payload["content"]
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return [payload]
    return []


def _search_tracks(
    session: requests.Session,
    search_text: str,
    *,
    page: int,
    size: int = SEARCH_PAGE_SIZE,
) -> list[dict[str, Any]]:
    payload = _request_json(
        session,
        "/track/search",
        params={"searchText": search_text, "size": size, "page": page},
    )
    return _content(payload)


def _get_audio_features(
    session: requests.Session,
    track_id: str,
) -> dict[str, Any] | None:
    try:
        payload = _request_json(session, f"/track/{track_id}/audio-features")
    except requests.HTTPError as error:
        if error.response is not None and error.response.status_code == 404:
            return None
        raise

    if isinstance(payload, dict):
        return payload
    return None


def extract_reccobeats_data(
    *,
    target_tracks: int = DEFAULT_TARGET_TRACKS,
    search_terms: list[str] | None = None,
) -> Path:
    """Obtiene aproximadamente target_tracks canciones desde ReccoBeats."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = RAW_PATH.with_suffix(".json.part")

    terms = search_terms or DEFAULT_SEARCH_TERMS
    if not terms:
        raise ValueError("Se requiere al menos un termino de busqueda para ReccoBeats.")

    print(f"Buscando tracks hasta reunir {target_tracks} canciones unicas...")

    session = requests.Session()
    tracks_by_id: dict[str, dict[str, Any]] = {}

    page = 0
    while len(tracks_by_id) < target_tracks:
        found_new_track = False
        for term in terms:
            if len(tracks_by_id) >= target_tracks:
                break

            tracks = _search_tracks(session, term, page=page)
            for track in tracks:
                track_id = track.get("id")
                if track_id and track_id not in tracks_by_id:
                    tracks_by_id[track_id] = track
                    found_new_track = True
                if len(tracks_by_id) >= target_tracks:
                    break

            time.sleep(REQUEST_PAUSE_SECONDS)

        if not found_new_track:
            break
        page += 1

        if len(tracks_by_id) >= target_tracks:
            break

    if not tracks_by_id:
        raise RuntimeError("ReccoBeats no devolvio tracks para los terminos configurados.")

    print(f"Tracks unicos encontrados: {len(tracks_by_id)}")
    print("Descargando audio features por track...")

    records: list[dict[str, Any]] = []
    for index, (track_id, track) in enumerate(tracks_by_id.items(), start=1):
        features = _get_audio_features(session, track_id)
        if features is not None:
            records.append({"track": track, "audio_features": features})

        if index % 25 == 0:
            print(f"Audio features consultadas: {index}/{len(tracks_by_id)}")
        time.sleep(REQUEST_PAUSE_SECONDS)

    if not records:
        raise RuntimeError("No se pudieron obtener audio features desde ReccoBeats.")

    raw_payload = {
        "source": "ReccoBeats API",
        "base_url": BASE_URL,
        "target_tracks": target_tracks,
        "search_terms": terms,
        "records": records,
    }

    with temporary_path.open("w", encoding="utf-8") as output_file:
        json.dump(raw_payload, output_file, ensure_ascii=False, indent=2)

    temporary_path.replace(RAW_PATH)
    print(f"Raw ReccoBeats guardado correctamente: {RAW_PATH}")
    return RAW_PATH
