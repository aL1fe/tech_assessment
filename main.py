import logging
import signal
from multiprocessing import synchronize, Queue, Process, Event

from module_capture import CaptureModule
from module_processing import ProcessingModule
from module_reporter import ReporterModule


logging.basicConfig(level=logging.INFO, format='%(asctime)s [Main] %(message)s')
logger = logging.getLogger("Main")


def run_stage1_capture(metadata_queue: Queue, stop_event: synchronize.Event):
    capture = CaptureModule(metadata_queue, stop_event)
    capture.run()


def run_stage2_processing(metadata_queue: Queue, result_queue: Queue, stop_event: synchronize.Event):
    processor = ProcessingModule(metadata_queue, result_queue, stop_event)
    processor.run()


def run_stage3_reporter(result_queue: Queue, stop_event: synchronize.Event):
    reporter = ReporterModule(result_queue, stop_event)
    reporter.run()
   

def main():
    stop_event = Event()
    def stop_gracefully(signum=None, frame=None):
        logger.info("Pipeline is stopping...")
        stop_event.set()
        for p in [capture_process, processing_process, reporter_process]:
            p.join()
        logger.info("All processes stopped.")
    signal.signal(signal.SIGTERM, stop_gracefully)
    signal.signal(signal.SIGINT, stop_gracefully)

    metadata_queue = Queue(maxsize=100)
    result_queue = Queue(maxsize=100)

    capture_process = Process(
        target=run_stage1_capture,
        args=(metadata_queue, stop_event,),
        name="CaptureProcess"
    )
    
    processing_process = Process(
        target=run_stage2_processing,
        args=(metadata_queue, result_queue, stop_event,),
        name="ProcessingProcess"
    )

    reporter_process = Process(
        target=run_stage3_reporter,
        args=(result_queue, stop_event,),
        name="ReporterProcess"
    )

    try:
        capture_process.start()
        logger.info(f"Capture process started (PID: {capture_process.pid})")

        processing_process.start()
        logger.info(f"Processing process started (PID: {processing_process.pid})")

        reporter_process.start()
        logger.info(f"Reporter process started (PID: {reporter_process.pid})")

        while capture_process.is_alive():
            capture_process.join(timeout=1.0)
    finally:
        stop_gracefully()
       

if __name__ == "__main__":
    main()
