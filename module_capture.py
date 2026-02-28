import logging
import time
import threading
from multiprocessing import Queue
from multiprocessing.synchronize import Event

from fake_camera import FakeCamera, CameraError
from ring_buffer import RingBuffer
from config import settings


logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Capture")


class CaptureModule:
    def __init__(self, metadata_queue: Queue, stop_event: Event):
        self.metadata_queue = metadata_queue
        self._stop_event = stop_event


    def _camera_worker(self, camera_id: str, fps: int):
        buffer = RingBuffer(camera_id, capacity=10, shape=(settings.HEIGHT, settings.WIDTH, settings.CHANNELS))
        cam = None
        retries = 0
        try:
            while not self._stop_event.is_set():
                try:
                    if cam is None:
                        start_time = time.monotonic()
                        cam = FakeCamera(camera_id=camera_id, fps=fps)
                        logger.info(f"[Capture] {camera_id} connected")                    
                    else:
                        frame = cam.read()
                        retries = 0
                        
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
                    uptime = time.monotonic() - start_time  # type: ignore
                    logger.error(f"[{camera_id}] Disconnected after {uptime:.1f}s: {e}")
                    if cam:
                        cam.release()
                        cam = None
                    retries += 1
                    if retries >= settings.MAX_RECONNECT:
                        logger.critical(f"[{camera_id}] Camera permanently unavailable.")
                        break
                    delay = min(settings.MAX_DELAY, settings.BASE_DELAY * 2 ** retries)
                    logger.info(f"[{camera_id}] Will reconnect in {delay:.1f}s")
                    time.sleep(delay)
                # TODO develop mechanism to restart camera manually
                except Exception as e:
                    logger.exception(f"Critical error in thread {camera_id}: {e}")
                    break

            if cam:
                cam.release()

        finally:
            buffer.close()
            logger.info(f"[{camera_id}] Worker thread exited")


    def run(self):
        logger.info("Stage 1: Capture process started")
        for cam_id, cfg in settings.CAMERA_CFG.items():
            threading.Thread(
                target=self._camera_worker, 
                args=(cam_id, cfg.fps), 
            ).start()
            