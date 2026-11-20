
from __future__ import annotations

import cv2
import numpy as np


def create_motion_detector():
    """Prepara o detetor de movimento e o kernel."""

    subtractor = cv2.createBackgroundSubtractorMOG2(
        history=600,        # Histórico usado para atualizar o fundo
        varThreshold=48,    # Tolerância estatística a diferenças
        detectShadows=True, # Identifica sombras separadamente
    )

    # Matriz 5x5 usada para limpar e expandir regiões
    kernel = np.ones((5, 5), np.uint8)

    return subtractor, kernel


def detect_motion(
    frame: np.ndarray,
    subtractor,
    kernel: np.ndarray,
    min_area: int,
) -> list[tuple[int, int, int, int]]:
    """Deteta movimento e devolve retângulos."""

    # MOG2: compara o frame com o modelo do fundo
    mask = subtractor.apply(frame)

    # Mantém primeiro plano (255) e exclui sombras (127)
    _, mask = cv2.threshold(
        mask, 200, 255, cv2.THRESH_BINARY
    )

    # Abertura morfológica: remove ruído pequeno
    mask = cv2.morphologyEx(
        mask, cv2.MORPH_OPEN, kernel
    )

    # Expande regiões brancas uma vez
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Encontra os limites externos das regiões brancas
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    rectangles = []

    for contour in contours:
        # Ignora regiões com área inferior ao mínimo
        if cv2.contourArea(contour) >= min_area:
            # Guarda (x, y, largura, altura)
            rectangles.append(cv2.boundingRect(contour))

    return rectangles


def zone_for_x(x: int, width: int) -> int:
    """Determina a zona pela coordenada horizontal."""

    # Divide a largura em três: zonas 0, 1 e 2
    return min(2, max(0, x * 3 // width))


def group_boxes(
    boxes: list[tuple[int, int, int, int]],
    width: int,
) -> list[list[list[int]]]:
    """Agrupa os retângulos pelas três zonas."""

    by_zone: list[list[list[int]]] = [[], [], []]

    for x, y, bw, bh in boxes:
        # Calcula o centro horizontal da caixa
        center_x = x + bw // 2

        # Descobre em que zona está esse centro
        zone = zone_for_x(center_x, width)

        by_zone[zone].append([x, y, bw, bh])

    return by_zone


def draw_zone(
    output: np.ndarray,
    index: int,
    name: str,
    color: tuple[int, int, int],
) -> None:
    """Desenha o limite e o nome de cada zona."""

    h, w = output.shape[:2]

    # Define o início e o fim do terço horizontal
    start_x = index * w // 3
    end_x = (index + 1) * w // 3

    cv2.rectangle(
        output, (start_x, 0),
        (end_x - 1, h - 1), color, 2
    )

    cv2.putText(
        output,
        f"ZONA {index+1} - {name.upper()}",
        (start_x + 8, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55, color, 2, cv2.LINE_AA,
    )


def draw_boxes(
    output: np.ndarray,
    boxes: list[list[int]],
    color: tuple[int, int, int],
) -> None:
    """Desenha as caixas das deteções."""

    for x, y, bw, bh in boxes:
        cv2.rectangle(
            output,
            (x, y),
            (x + bw, y + bh),
            color,
            2,
        )
