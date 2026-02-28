import logging
import time
import threading
from multiprocessing import Queue
from multiprocessing.synchronize import Event

from fake_camera import FakeCamera, CameraError
from shared_ring_buffer import CameraBuffer
from config import settings


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Capture")


class CaptureModule:
    def __init__(self, metadata_queue: Queue, stop_event: Event):
        self.metadata_queue = metadata_queue
        self._stop_event = stop_event


    def _camera_worker(self, camera_id: str, fps: int):
        buffer = CameraBuffer(camera_id, capacity=10, shape=(settings.HEIGHT, settings.WIDTH, settings.CHANNELS))
        
        retries = 0
        try:
            while not self._stop_event.is_set():
                start_time = time.monotonic()
                cam = FakeCamera(camera_id=camera_id, fps=fps)
                try:
                    logger.info(f"[Capture] {camera_id} connected")                    
                    while not self._stop_event.is_set():
                        frame = cam.read()
                        
                        # Save every x frame to prevent overload Porcessing service
                        if cam.frame_count % settings.FRAME_SUBSAMPLE == 0:
                            slot_idx = buffer.put(frame)
                            
                            # TODO: Ring buffer overwrites slots in circular order.
                            # If Processing is slower than Capture, metadata in the queue
                            # may reference a slot that has already been overwritten.
                            # Add frame_id validation or backpressure mechanism to prevent stale reads.
                            if not self.metadata_queue.full():
                                self.metadata_queue.put({
                                    "cam_id": camera_id,
                                    "slot": slot_idx,
                                    "ts": time.time(),
                                    "frame_num": cam.frame_count
                                })
                            
                except CameraError as e:
                    uptime = time.monotonic() - start_time
                    logger.error(f"[{camera_id}] Disconnected after {uptime:.1f}s: {e}")
                    retries = 0 if uptime >= settings.STABLE_THRESHOLD else retries + 1
                    delay = min(settings.MAX_DELAY, settings.BASE_DELAY * 2 ** retries)
                    logger.info(f"[{camera_id}] Reconnect in {delay:.1f}s")
                    time.sleep(delay)
                # TODO develop mechanism to restart camera manually
                except Exception as e:
                    logger.exception(f"Critical error in thread {camera_id}: {e}")
                    break
                finally:
                    if cam:
                        cam.release()

        finally:
            buffer.close()
            logger.info(f"[{camera_id}] Worker thread exited")


    def run(self):
        logger.info("Stage 1: Capture process started")
        threads = []
        
        for cam_id, cfg in settings.CAMERA_CFG.items():
            t = threading.Thread(
                target=self._camera_worker, 
                args=(cam_id, cfg.fps), 
                daemon=True
            )
            t.start()
            threads.append(t)
            
        try:
            while any(t.is_alive() for t in threads):
                time.sleep(0.5)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Capture process received stop signal")
        finally:
            self._stop_event.set()
            
            for t in threads:
                t.join(timeout=1.0)
            
            logger.info("Stage 1: Capture process finished")
            