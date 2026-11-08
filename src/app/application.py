"""Main application loop and component coordination."""

from __future__ import annotations

from time import monotonic

import cv2

from app.animations import render_zone
from app.assets import load_animations
from app.camera import CameraCapture
from app.config import AppConfig
from app.events import create_event_tracker, expire_zone, finish_events, record_motion
from app.logger import AppLogger
from app.motion import create_motion_detector, detect_motion
from app.recorder import EvidenceRecorder
from app.zones import draw_boxes, draw_zone, group_boxes


class VisualApplication:
    """Coordinate capture, detection, rendering, and evidence recording."""

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = AppLogger()
        self.camera = CameraCapture(config.camera_index)
        self.subtractor, self.motion_kernel = create_motion_detector()

    def run(self) -> None:
        """Run the camera loop and release resources when it ends."""
        assets = load_animations(self.config.assets_dir, self.config.zone_sprites, self.logger)
        recorder = EvidenceRecorder(
            self.config.root,
            self.config.evidence_dir,
            self.config.fps,
            self.logger,
        )
        events = create_event_tracker(
            recorder.json_path,
            recorder.video_path,
            self.config.root,
            zone_count=3,
            hold_seconds=self.config.hold_seconds,
            logger=self.logger,
        )

        self.camera.open()
        frame_no = 0
        starting_time = monotonic()

        try:
            while True:
                ok, camera_frame = self.camera.read()
                if not ok:
                    self.logger.info("Webcam deixou de fornecer frames; a terminar.", "yellow")
                    break

                height, width = camera_frame.shape[:2]
                recorder.start_if_needed(width, height)
                now = monotonic()
                duration_so_far = now - starting_time
                frame_no += 1

                boxes = detect_motion(
                    camera_frame, self.subtractor, self.motion_kernel, self.config.min_area
                )
                by_zone = group_boxes(boxes, width)
                output = camera_frame.copy()

                for index, name in enumerate(self.config.zone_sprites):
                    color = self.config.zone_colors[index]
                    draw_zone(output, index, name, color)

                    # Ignore detections during background warmup.
                    if frame_no > self.config.warmup and by_zone[index]:
                        x, y, bw, bh = max(by_zone[index], key=lambda box: box[2] * box[3])
                        center = (x + bw // 2, y + bh // 2)

                        play_time, direction = record_motion(
                            events,
                            index,
                            name,
                            by_zone[index],
                            center,
                            now,
                            duration_so_far,
                        )
                        render_zone(
                            assets,
                            output,
                            index,
                            self.config.zone_sprites[name],
                            center,
                            max(bw, bh),
                            direction,
                            play_time,
                        )

                    expire_zone(events, index, now)
                    if frame_no > self.config.warmup:
                        draw_boxes(output, by_zone[index], color)

                if frame_no <= self.config.warmup:
                    cv2.putText(
                        output,
                        f"A estabilizar fundo: {self.config.warmup-frame_no} frames",
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

                recorder.write(output)
                cv2.imshow("Computacao Visual - OpenCV / Blender", output)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("s"):
                    recorder.screenshot(output)
        finally:
            # Finalize events before closing capture and recording resources.
            now = monotonic()
            try:
                finish_events(events, now)
            finally:
                self.camera.release()
                recorder.close()
                cv2.destroyAllWindows()
            self.logger.info(
                f"Terminado. {len(events['events'])} eventos em "
                f"{recorder.json_path.relative_to(self.config.root)}",
                "green",
            )
