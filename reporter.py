# reporter.py
import logging
from queue import Empty
from multiprocessing import Queue
from multiprocessing.synchronize import Event


logger = logging.getLogger("Reporter")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s [Reporter] %(message)s'))

file_handler = logging.FileHandler("reporter.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s [Reporter] %(message)s'))

logger.addHandler(console_handler)
logger.addHandler(file_handler)


class ReporterModule:
    def __init__(self, result_queue: Queue, stop_event: Event):
        self.result_queue = result_queue
        self._stop_event = stop_event


    def run(self):
        logger.info("Stage 3: Reporter started")

        while not self._stop_event.is_set():
            try:
                result = self.result_queue.get(timeout=0.5)

                logger.info(
                    f"[{result['cam_id']}] "
                    f"frame={result['frame_num']} "
                    f"latency={result['latency']:.3f}s"
                )
            except Empty:
                continue
            except Exception as e:
                logger.exception(f"Critical error in ReporterModule: {e}")

        logger.info("Stage 3: Reporter finished")
