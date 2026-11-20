
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.logger import log


def create_event_tracker(
    path: Path,
    video_path: Path,
    root: Path,
    zone_count: int,
    hold_seconds: float,
) -> dict:
    """Prepara o controlo dos eventos de cada zona."""

    zones = []

    for _ in range(zone_count):
        zones.append({
            "event": None,            # Sem evento ativo
            "last_seen": float("-inf"), # Último movimento
            "last_centroid": None,     # Centro anterior
        })

    tracker = {
        "path": path,               # Caminho do JSON
        "video_path": video_path,   # Caminho do vídeo
        "root": root,
        "hold_seconds": hold_seconds,
        "events": [],               # Eventos concluídos
        "zones": zones,
    }

    # Cria inicialmente um JSON vazio
    write_events(tracker)
    return tracker


def record_motion(
    tracker: dict,
    zone: int,
    zone_name: str,
    boxes: list[list[int]],
    center: tuple[int, int],
    now: float,
    video_seconds: float,
) -> tuple[float, int]:
    """Inicia/atualiza evento e calcula direção."""

    state = tracker["zones"][zone]
    state["last_seen"] = now

    # Cria evento se ainda não existir nesta zona
    if state["event"] is None:
        state["event"] = {
            "inicio": datetime.now().astimezone().isoformat(
                timespec="seconds"
            ),
            "duracao_segundos": 0.0,
            "zona": f"{zone+1} - {zone_name}",
            "ficheiro_gravado": (
                tracker["video_path"]
                .relative_to(tracker["root"])
                .as_posix()
            ),
            "bounding_boxes": [],
            "_start_mono": now, # Início para calcular duração
        }
        log(f"Movimento: zona {zone+1} ({zone_name})", "yellow")

    event = state["event"]

    # Regista até 25 amostras, com até 8 caixas cada
    if len(event["bounding_boxes"]) < 25:
        event["bounding_boxes"].append({
            "tempo_video_segundos": round(video_seconds, 2),
            "caixas": boxes[:8],
        })

    # Compara o centro atual com o anterior
    direction = 0

    if state["last_centroid"] is not None:
        dx = center[0] - state["last_centroid"][0]

        if dx > 5:
            direction = 1   # Movimento para a direita
        elif dx < -5:
            direction = -1  # Movimento para a esquerda

    state["last_centroid"] = center

    # Devolve tempo de animação e direção
    return now - event["_start_mono"], direction


def expire_zone(tracker: dict, zone: int, now: float) -> None:
    """Termina o evento quando a zona fica inativa."""

    state = tracker["zones"][zone]

    if (
        state["event"] is not None
        and now - state["last_seen"] > tracker["hold_seconds"]
    ):
        end_event(tracker, zone, now)


def end_event(tracker: dict, zone: int, now: float) -> None:
    """Conclui o evento e atualiza o JSON."""

    state = tracker["zones"][zone]
    event = state["event"]

    if event is None:
        return

    # Calcula a duração total em segundos
    event["duracao_segundos"] = round(
        max(0.0, now - event.pop("_start_mono")), 2
    )

    tracker["events"].append(event)
    write_events(tracker)  # Guarda eventos concluídos

    log(
        f"Zona {event['zona']}: evento gravado "
        f"({event['duracao_segundos']} s)",
        "green",
    )

    # Liberta o estado para um novo evento
    state["event"] = None
    state["last_centroid"] = None


def finish_events(tracker: dict, now: float) -> None:
    """Termina eventos ativos quando o programa fecha."""

    for zone, state in enumerate(tracker["zones"]):
        if state["event"] is not None:
            end_event(tracker, zone, now)


def write_events(tracker: dict) -> None:
    """Grava a lista de eventos num ficheiro JSON."""

    path = tracker["path"]
    temp = path.with_suffix(".tmp")

    # Converte os eventos Python para texto JSON
    temp.write_text(
        json.dumps(
            tracker["events"],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # Substitui o JSON através de um ficheiro temporário
    temp.replace(path)
