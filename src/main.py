#!uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "numpy",
#   "opencv-python>=5.0,<6",
#   "rich",
# ]
# ///

from __future__ import annotations #linguagem Python, não do OpenCV


import json
from datetime import datetime
from pathlib import Path #caminhos que funcionam em diferentes computadores.
from time import monotonic #medir durações sem depender da hora do relógio

import cv2
import numpy as np


# -----------------------------------------------------------------------------
# Mensagens na consola (objetivo 5)
# -----------------------------------------------------------------------------
# Se a biblioteca rich estiver instalada, as mensagens aparecem com cores.

try:
    from rich.console import Console
    console = Console()

    def info(msg: str, style: str = "cyan") -> None:
        """Mostra uma mensagem com hora e cor."""
        console.print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", style=style)
except ImportError:
    def info(msg: str, style: str = "cyan") -> None:
        """Alternativa sem cores quando rich não está disponível.""" #Caso contrário, o programa continua a funcionar usando print().
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")


# -----------------------------------------------------------------------------
# Pastas e associação de objetos a zonas
# -----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
EVIDENCIAS = ROOT / "evidencias"
SPRITES = {
    "esquerda": ("chair", "vase"),
    "centro": ("table",),               # A ordem das chaves define as três zonas: esquerda, centro e direita.
    "direita": ("dish", "glass"),
}

ZONES = tuple(SPRITES)
COLORS = ((255, 180, 60), (60, 220, 100), (220, 140, 230))


def load_assets() -> dict[str, list[np.ndarray]]: #Lê uma vez as sequências PNG de todos os objetos necessários.

    animations: dict[str, list[np.ndarray]] = {}

    # Percorremos todos os nomes dos objetos, sem repetir os que possam
    # aparecer em mais do que uma zona (dict.fromkeys mantém a ordem).
    for name in dict.fromkeys(n for group in SPRITES.values() for n in group):
        folder = ASSETS / name
        paths = sorted(folder.glob("*.png"))

        if not paths:
            raise FileNotFoundError(f"Sem PNGs em {folder}. Corre 'git pull' na raiz.")

        frames: list[np.ndarray] = []
        for path in paths:
            # IMREAD_UNCHANGED lê 4 canais (B, G, R e alfa) nos PNGs RGBA.
            img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
            if img is None or img.ndim != 3 or img.shape[2] != 4:
                raise ValueError(f"PNG sem canal alfa RGBA válido: {path}")
            frames.append(img)

        animations[name] = frames
        info(f"{name}: {len(frames)} frames RGBA")

    return animations


def overlay_rgba(frame: np.ndarray, sprite: np.ndarray,
                 center: tuple[int, int], side: int) -> None: #Coloca um PNG transparente por cima da imagem da câmara.

    # Tamanho mínimo para o objeto continuar visível.
    side = max(40, int(side))
    h0, w0 = sprite.shape[:2]

    # Ajustamos a largura pedida e mantemos a proporção original.
    dest_w = side
    dest_h = max(1, round(side * h0 / w0))
    image = cv2.resize(sprite, (dest_w, dest_h), interpolation=cv2.INTER_AREA)

    # Altura e largura da imagem da câmara.
    h, w = frame.shape[:2]

    # Converter o centro do objeto na posição do seu canto superior esquerdo.
    x = round(center[0] - dest_w / 2)
    y = round(center[1] - dest_h / 2)

    # Limitar o recorte às margens válidas da imagem.
    xa, ya = max(0, x), max(0, y)
    xb, yb = min(w, x + dest_w), min(h, y + dest_h)
    if xa >= xb or ya >= yb:
        return  # O objeto ficou totalmente fora da imagem.

    crop = image[ya - y:yb - y, xa - x:xb - x]

    #PL04: resultado = alfa * objeto + (1 - alfa) * fundo.
    alpha = crop[:, :, 3:4].astype(np.float32) / 255.0
    bg = frame[ya:yb, xa:xb].astype(np.float32)
    fg = crop[:, :, :3].astype(np.float32)

    # Voltamos a uint8 porque os píxeis do OpenCV usam inteiros de 0 a 255.
    frame[ya:yb, xa:xb] = np.clip(
        fg * alpha + bg * (1.0 - alpha), 0, 255
    ).astype(np.uint8)


def detect_motion(frame: np.ndarray, subtractor: cv2.BackgroundSubtractor,
                  min_area: int) -> list[tuple[int, int, int, int]]: #Deteta regiões diferentes do fundo e devolve caixas (x, y, w, h).

    # MOG2 produz uma máscara: fundo (0), sombras (127) e primeiro plano (255).
    mask = subtractor.apply(frame)

    # Consideramos apenas os píxeis acima de 200 para excluir sombras (127).
    _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

    # MORPH_OPEN retira pontos de ruído; dilate junta/engrossa manchas.
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.dilate(mask, kernel, iterations=2)

    # Encontramos os contornos externos das manchas da máscara.
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Ignoramos contornos muito pequenos e devolvemos os retângulos válidos.
    return [cv2.boundingRect(contour) for contour in contours
            if cv2.contourArea(contour) >= min_area]


def zone_for_x(x: int, width: int) -> int: #Escolhe a zona pela posição horizontal do centro do movimento.
    return min(2, max(0, x * 3 // width))


def write_events(path: Path, events: list[dict]) -> None: #Guarda os eventos num JSON legível (objetivo 5 do enunciado).
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def open_recorder(path: Path, fps: float, width: int, height: int) -> cv2.VideoWriter: #Abre o gravador MP4 das evidências (objetivo 5 do enunciado)."""
    # mp4v é o codec usado para escrever o vídeo com o VideoWriter.
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError("Não foi possível gravar MP4 (codec mp4v). Verifica OpenCV e a pasta evidencias/.")
    return writer


def main() -> None: #liga a câmera
    # -------------------------------------------------------------------------
    # Argumentos do terminal
    # -------------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="Cena interativa Blender + OpenCV")
    parser.add_argument("--camera", type=int, default=0, help="Índice da webcam (0, 1, ...)")
    parser.add_argument("--min-area", type=int, default=700, help="Área mínima de contorno em px²")
    parser.add_argument("--fps", type=float, default=24.0, help="FPS do MP4 gravado")
    parser.add_argument("--warmup", type=int, default=50, help="Frames iniciais para estabilizar MOG2")
    args = parser.parse_args()

    # -------------------------------------------------------------------------
    # Preparar os assets e os ficheiros de evidências
    # -------------------------------------------------------------------------
    assets = load_assets()
    EVIDENCIAS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = EVIDENCIAS / f"video_{stamp}.mp4"
    json_path = EVIDENCIAS / f"deteccoes_{stamp}.json"


    events: list[dict] = []
    write_events(json_path, events) #Json Válido

    # -------------------------------------------------------------------------
    # Abrir a webcam (PL04, secção 5, pág. 11)
    # No Windows tentamos DirectShow (CAP_DSHOW), com alternativa genérica.
    # -------------------------------------------------------------------------
    camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW) if hasattr(cv2, "CAP_DSHOW") else cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        camera.release()
        camera = cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        raise RuntimeError(f"Webcam {args.camera} indisponível. Experimenta --camera 1.")

#!!!
    writer: cv2.VideoWriter | None = None
    subtractor = cv2.createBackgroundSubtractorMOG2(history=400, varThreshold=48, detectShadows=True)
    active: list[dict | None] = [None, None, None]
    last_seen = [float("-inf")] * 3
    last_centroid: list[tuple[int, int] | None] = [None] * 3

    frame_no = 0
    starting_time = monotonic()
    hold_seconds = 0.65  # Tempo sem movimento antes de fechar um evento.
    duration_so_far = 0.0

    def end_event(z: int, now: float) -> None:
        """Termina uma deteção numa zona e guarda-a no JSON."""
        event = active[z]
        if event is None:
            return

        # monotonic mede o tempo decorrido com segurança, mesmo que a hora
        # do computador seja alterada enquanto o programa corre.
        event["duracao_segundos"] = round(max(0.0, now - event.pop("_start_mono")), 2)

        # O código guarda até 25 amostras das caixas; atualmente são as
        # PRIMEIRAS 25, não necessariamente a última leitura do movimento.
        events.append(event)
        write_events(json_path, events)
        info(f"Zona {event['zona']}: evento gravado ({event['duracao_segundos']} s)", "green")

        active[z] = None
        last_centroid[z] = None

    # -------------------------------------------------------------------------
    # Ciclo principal: um fotograma da webcam de cada vez
    # -------------------------------------------------------------------------
    try:
        while True:
            ok, camera_frame = camera.read()
            if not ok:
                info("Webcam deixou de fornecer frames; a terminar.", "yellow")
                break

            # A imagem fica espelhada, semelhante à pré-visualização da webcam.
            camera_frame = cv2.flip(camera_frame, 1)
            h, w = camera_frame.shape[:2]

            # Só abrimos o MP4 quando conhecemos a resolução real da câmara.
            if writer is None:
                writer = open_recorder(video_path, args.fps, w, h)
                info(f"Vídeo: {video_path.relative_to(ROOT)}", "green")

            now = monotonic()
            duration_so_far = now - starting_time
            frame_no += 1

            # -----------------------------------------------------------------
            # Deteção MOG2 e escolha da zona pelo centro do contorno
            # -----------------------------------------------------------------
            boxes = detect_motion(camera_frame, subtractor, args.min_area)

            # Uma lista de caixas para cada uma das 3 zonas.
            by_zone: list[list[list[int]]] = [[], [], []]
            centroids: list[tuple[int, int] | None] = [None, None, None]

            for x, y, bw, bh in boxes:
                cx, cy = x + bw // 2, y + bh // 2  # centro da caixa
                z = zone_for_x(cx, w)
                by_zone[z].append([x, y, bw, bh])

            # Desenhamos sobre uma cópia para não interferir com a deteção.
            output = camera_frame.copy()

            # -----------------------------------------------------------------
            # Desenhar as zonas e reagir aos movimentos
            # -----------------------------------------------------------------
            for i, name in enumerate(ZONES):
                # Três colunas de largura aproximadamente igual.
                start_x, end_x = i * w // 3, (i + 1) * w // 3
                cv2.rectangle(output, (start_x, 0), (end_x - 1, h - 1), COLORS[i], 2)
                cv2.putText(output, f"ZONA {i+1} - {name.upper()}", (start_x + 8, 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, COLORS[i], 2, cv2.LINE_AA)

                # Durante o warmup não desencadeamos eventos: o MOG2 está a
                # aprender o fundo. Depois basta existir uma caixa nesta zona.
                if frame_no > args.warmup and by_zone[i]:
                    # Se há várias caixas, escolhemos a maior para posicionar a animação; continuamos a guardar as restantes no evento.
                    x, y, bw, bh = max(by_zone[i], key=lambda box: box[2] * box[3])
                    center = (x + bw // 2, y + bh // 2)
                    centroids[i] = center
                    last_seen[i] = now

                    if active[i] is None:
                        # Novo evento: hora ISO 8601, zona, vídeo e caixas.
                        # Objetivo 5 do enunciado.
                        active[i] = {
                            "inicio": datetime.now().astimezone().isoformat(timespec="seconds"),
                            "duracao_segundos": 0.0,
                            "zona": f"{i+1} - {name}",
                            "ficheiro_gravado": str(video_path.relative_to(ROOT)).replace("\\", "/"),
                            "bounding_boxes": [],
                            "_start_mono": now,  # campo interno, retirado ao terminar
                        }
                        info(f"Movimento: zona {i+1} ({name})", "yellow")

                    event = active[i]
                    if len(event["bounding_boxes"]) < 25:
                        # Amostra: instante do vídeo e até 8 caixas neste instante.
                        event["bounding_boxes"].append({
                            "tempo_video_segundos": round(duration_so_far, 2),
                            "caixas": by_zone[i][:8],
                        })

                    # Comparar a posição horizontal atual com a anterior.
                    # O valor -1/0/+1 indica movimento à esquerda/parado/direita.
                    direction = 0
                    if last_centroid[i] is not None:
                        dx = center[0] - last_centroid[i][0]
                        direction = 1 if dx > 5 else (-1 if dx < -5 else 0)
                    last_centroid[i] = center

                    # O tempo desde o início do evento controla o avanço dos PNGs.
                    play_time = now - event["_start_mono"]
                    extent = max(bw, bh)

                    for obj_index, object_name in enumerate(SPRITES[name]):
                        imgs = assets[object_name]

                        if i == 0:
                            # Zona esquerda: os objetos acompanham o centro do movimento. 

                            pos = (center[0] + (-40 if obj_index == 0 else 52), center[1])
                            side = 145 if obj_index == 0 else 95
                            speed = 24
                        elif i == 1:
                            # Zona central: o objeto aumenta ou diminui com o
                            
                            pos = (center[0], center[1])
                            side = min(235, max(100, int(extent * 0.95)))
                            speed = 24
                        else:
                            # Zona direita: a VELOCIDADE da animação depende do
                        
                            pos = (center[0] + (-38 if obj_index == 0 else 43), center[1])
                            side = 135 if obj_index == 0 else 105
                            speed = 35 if direction > 0 else (12 if direction < 0 else 24)

                        # PL04, secção 4: o módulo % volta ao início da sequência.
                        # Aqui usamos o tempo decorrido e a velocidade escolhida.
                        frame_id = int(play_time * speed) % len(imgs)
                        overlay_rgba(output, imgs[frame_id], pos, side)

                # Se deixou de haver movimento nesta zona durante 0,65 s,
                # terminamos o evento. A animação atual só aparece enquanto
                # existir deteção no bloco acima (não fica durante o hold).
                if active[i] is not None and now - last_seen[i] > hold_seconds:
                    end_event(i, now)

                # Caixas dos movimentos visíveis, como na PL04, secção 7.
                for x, y, bw, bh in by_zone[i]:
                    if frame_no > args.warmup:
                        cv2.rectangle(output, (x, y), (x + bw, y + bh), COLORS[i], 2)

            # Texto informativo durante o arranque do modelo MOG2.
            if frame_no <= args.warmup:
                cv2.putText(output, f"A estabilizar fundo: {args.warmup-frame_no} frames",
                            (12, h - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (30, 220, 240), 2)
            cv2.putText(output, "Q: sair | S: captura", (12, h - 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

            # -----------------------------------------------------------------
            # Guardar vídeo e mostrar a janela (objetivo 5)
            # -----------------------------------------------------------------
            writer.write(output)
            cv2.imshow("Computacao Visual - OpenCV / Blender", output)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("s"):
                # Uma imagem de evidência com data/hora no nome.
                path = EVIDENCIAS / f"captura_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                cv2.imwrite(str(path), output)
                info(f"Captura: {path.relative_to(ROOT)}", "green")
    finally:
        # ---------------------------------------------------------------------
        # Encerrar corretamente (PL04, secção 5)
        # ---------------------------------------------------------------------
        now = monotonic()
        for i in range(3):
            if active[i] is not None:
                end_event(i, now)
        camera.release()
        if writer is not None:
            writer.release()
        cv2.destroyAllWindows()
        info(f"Terminado. {len(events)} eventos em {json_path.relative_to(ROOT)}", "green")


# Este bloco impede que a webcam arranque só por importar este módulo.
if __name__ == "__main__":
    main()