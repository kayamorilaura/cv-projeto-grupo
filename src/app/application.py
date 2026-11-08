"""Main application loop and component coordination."""

from __future__ import annotations

from time import monotonic

import cv2

from app.animations import render_zone
from app.assets import load_animations
from app.camera import open_camera, read_camera
from app.events import create_event_tracker, expire_zone, finish_events, record_motion
from app.logger import log
from app.motion import create_motion_detector, detect_motion
from app.recorder import (
    close_recorder, create_recorder, save_screenshot, start_recording, write_frame,
)
from app.zones import draw_boxes, draw_zone, group_boxes


def update_zones(output, by_zone, frame_no, config, events, assets, now, video_seconds):
    """Update each zone and draw its current reaction."""
    for index, name in enumerate(config['zone_sprites']):
        color = config['zone_colors'][index]
        draw_zone(output, index, name, color)

        # Ignore detections during background warmup.
        if frame_no > config['warmup'] and by_zone[index]:
            x, y, bw, bh = max(by_zone[index], key=lambda box: box[2] * box[3])
            center = (x + bw // 2, y + bh // 2)

            play_time, direction = record_motion(
                events,
                index,
                name,
                by_zone[index],
                center,
                now,
                video_seconds,
            )
            render_zone(
                assets,
                output,
                index,
                config['zone_sprites'][name],
                center,
                max(bw, bh),
                direction,
                play_time,
            )

        expire_zone(events, index, now)
        if frame_no > config['warmup']:
            draw_boxes(output, by_zone[index], color)


def run_application(config: dict) -> None:
    """Run the camera loop and release resources when it ends."""
    subtractor, motion_kernel = create_motion_detector()
    assets = load_animations(config['assets_dir'], config['zone_sprites'])
    recorder = create_recorder(
        config['root'],
        config['evidence_dir'],
        config['fps'],
    )
    events = create_event_tracker(
        recorder['json_path'],
        recorder['video_path'],
        config['root'],
        zone_count=3,
        hold_seconds=config['hold_seconds'],
    )

    camera = open_camera(config['camera_index'])
    frame_no = 0
    starting_time = monotonic()

    try:
        while True:
            ok, camera_frame = read_camera(camera)
            if not ok:
                log("Webcam deixou de fornecer frames; a terminar.", "yellow")
                break

            height, width = camera_frame.shape[:2]
            start_recording(recorder, width, height)
            now = monotonic()
            duration_so_far = now - starting_time
            frame_no += 1

            boxes = detect_motion(
                camera_frame, subtractor, motion_kernel, config['min_area']
            )
            by_zone = group_boxes(boxes, width)
            output = camera_frame.copy()

            update_zones(
                output, by_zone, frame_no, config, events, assets, now, duration_so_far
            )

            if frame_no <= config['warmup']:
                cv2.putText(
                    output,
                    f"A estabilizar fundo: {config['warmup']-frame_no} frames",
                    (12, height - 38),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (30, 220, 240),
                    2,
                )
            cv2.putText(
                output,
                "Q: sair | S: captura",
                (12, height - 13),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2,
            )

            write_frame(recorder, output)
            cv2.imshow("Computacao Visual - OpenCV / Blender", output)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            if key == ord("s"):
                save_screenshot(recorder, output)
    finally:
        # Finalize events before closing capture and recording resources.
        now = monotonic()
        try:
            finish_events(events, now)
        finally:
            camera.release()
            close_recorder(recorder)
            cv2.destroyAllWindows()
        log(
            f"Terminado. {len(events['events'])} eventos em "
            f"{recorder['json_path'].relative_to(config['root'])}",
            "green",
        )
