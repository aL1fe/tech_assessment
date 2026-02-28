# processing.py
import logging
import time
import cv2
from queue import Empty
import numpy as np
from multiprocessing import Queue
from multiprocessing.synchronize import Event
from ring_buffer import RingBuffer
from config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s [Processing] %(message)s')
logger = logging.getLogger("Processing")


class ProcessingModule:
    def __init__(self, metadata_queue: Queue, result_queue: Queue, stop_event: Event):
        self.metadata_queue = metadata_queue
        self.result_queue = result_queue
        self._stop_event = stop_event


    def process_frame(self, frame: np.ndarray):
        frame_resized = cv2.resize(frame, (640, 480))  # Resize to 640x480
        frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)  # Convert to grayscale
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
                buffer = RingBuffer(cam_id, capacity=10, shape=(settings.HEIGHT, settings.WIDTH, settings.CHANNELS))
                frame = buffer.get_frame(slot)

                # start_proc = time.time()
                processed_frame = self.process_frame(frame)
                end_proc = time.time()

                processing_latency = end_proc - metadata["ts"]

                self.result_queue.put({
                    "cam_id": cam_id,
                    "frame_num": frame_num,
                    "capture_ts": metadata["ts"],
                    "processed_ts": end_proc,
                    "latency": processing_latency
                })

                logger.info(f"[{cam_id}] slot={slot}, frame_num={frame_num} processed_frame.shape={processed_frame.shape}")
                logger.info(f"[{cam_id}] Processed frame {metadata['frame_num']}")

                buffer.close()  # Close shm handle for this access
            except Empty:
                continue
            except Exception as e:
                logger.exception(f"Critical error in ProcessingModule: {e}")

        logger.info("Stage 2: Processing finished")
