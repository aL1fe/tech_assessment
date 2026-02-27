# processing.py
import logging
import time
import cv2
import numpy as np
from multiprocessing import Queue
from multiprocessing.synchronize import Event
from shared_ring_buffer import CameraBuffer
from config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s [Processing] %(message)s')
logger = logging.getLogger("Processing")


class ProcessingModule:
    def __init__(self, metadata_queue: Queue, stop_event: Event):
        self.metadata_queue = metadata_queue
        self._stop_event = stop_event


    def process_frame(self, frame: np.ndarray):
        # Resize to 640x480
        frame_resized = cv2.resize(frame, (640, 480))
        # Convert to grayscale
        frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        time.sleep(0.1)  # Simulate inference
        return frame_gray
    

    def run(self):
        logger.info("Stage 2: Processing started")
        while not self._stop_event.is_set():
            try:
                metadata = self.metadata_queue.get(timeout=0.5)
                cam_id = metadata["cam_id"]
                slot = metadata["slot"]
                frame_num = metadata["frame_num"]

                # Get frame from shared memory buffer
                buffer = CameraBuffer(cam_id, capacity=10, shape=(settings.HEIGHT, settings.WIDTH, settings.CHANNELS))
                frame = buffer.get_frame(slot)

                processed_frame = self.process_frame(frame)
                logger.info(f"[{cam_id}] slot={slot}, frame_num={frame_num} processed_frame.shape={processed_frame.shape}")
                # TODO: send processed_frame to Stage 3 Reporter
                logger.info(f"[{cam_id}] Processed frame {metadata['frame_num']}")

                buffer.close()  # Close shm handle for this access

            except Exception as e:
                # Timeout or other errors
                continue

        logger.info("Stage 2: Processing finished")
