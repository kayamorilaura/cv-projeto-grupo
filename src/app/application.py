"""Main application loop and component coordination."""

from __future__ import annotations

from time import monotonic

import cv2

from app.animations import AnimationRenderer
from app.assets import AssetLoader
from app.camera import CameraCapture
from app.config import AppConfig
from app.events import EventTracker
from app.logger import AppLogger
from app.motion import MotionDetector
from app.recorder import EvidenceRecorder
from app.zones import ZoneManager


class VisualApplication:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.logger = AppLogger()
        self.camera = CameraCapture(config.camera_index)
        self.motion_detector = MotionDetector(config.min_area)
        self.zone_manager = ZoneManager(tuple(config.zone_sprites), config.zone_colors)
        self.asset_loader = AssetLoader(config.assets_dir, config.zone_sprites, self.logger)

    def run(self) -> None:
        assets = self.asset_loader.load()
        renderer = AnimationRenderer(assets)
        recorder = EvidenceRecorder(
            self.config.root,
            self.config.evidence_dir,
            self.config.fps,
            self.logger,
        )
        events = EventTracker(
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

                boxes = self.motion_detector.detect(camera_frame)
                by_zone = self.zone_manager.group_boxes(boxes, width)
                output = camera_frame.copy()

                for index, name in enumerate(self.zone_manager.names):
                    self.zone_manager.draw_zone(output, index)

                    if frame_no > self.config.warmup and by_zone[index]:
                        x, y, bw, bh = max(by_zone[index], key=lambda box: box[2] * box[3])
                        center = (x + bw // 2, y + bh // 2)

                        play_time, direction = events.record_motion(
                            index,
                            name,
                            by_zone[index],
                            center,
                            now,
                            duration_so_far,
                        )
                        renderer.render_zone(
                            output,
                            index,
                            self.config.zone_sprites[name],
                            center,
                            max(bw, bh),
                            direction,
                            play_time,
                        )

                    events.expire_zone(index, now)
                    if frame_no > self.config.warmup:
                        self.zone_manager.draw_boxes(output, index, by_zone[index])

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
            now = monotonic()
            try:
                events.finish(now)
            finally:
                self.camera.release()
                recorder.close()
                cv2.destroyAllWindows()
            self.logger.info(
                f"Terminado. {len(events.events)} eventos em "
                f"{recorder.json_path.relative_to(self.config.root)}",
                "green",
            )
