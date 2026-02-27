import logging
from multiprocessing import synchronize, Queue, Process, Event

from capture import CaptureModule
from processing import ProcessingModule


logging.basicConfig(level=logging.INFO, format='%(asctime)s [Main] %(message)s')
logger = logging.getLogger("Main")


def run_stage1_capture(metadata_queue):
    capture = CaptureModule(metadata_queue=metadata_queue)
    capture.run()


def run_stage2_processing(metadata_queue: Queue, stop_event: synchronize.Event):
    processor = ProcessingModule(metadata_queue, stop_event)
    processor.run()
    

def shutdown_process(proc, queue):
    if proc.is_alive():
        logger.info(f"Terminating {proc.name}...")
        queue.close()
        queue.cancel_join_thread() 
        
        proc.terminate()
        proc.join(timeout=2)
        if proc.is_alive():
            proc.kill()


def main():
    stop_event = Event()
    metadata_queue = Queue(maxsize=100)

    capture_process = Process(
        target=run_stage1_capture,
        args=(metadata_queue,),
        name="CaptureProcess"
    )
    
    processing_process = Process(
        target=run_stage2_processing,
        args=(metadata_queue, stop_event,),
        name="ProcessingProcess"
    )

    try:
        capture_process.start()
        logger.info(f"Capture process started (PID: {capture_process.pid})")

        processing_process.start()
        logger.info(f"Processing process started (PID: {processing_process.pid})")

        # reporter_process.start()

        while capture_process.is_alive():
            capture_process.join(timeout=1.0)

    except KeyboardInterrupt:
        logger.info("[Main] Stopping...")

    finally:
        stop_event.set()
        shutdown_process(capture_process, metadata_queue)  
        shutdown_process(processing_process, metadata_queue)    
        logger.info("Pipeline stopped.")
       

if __name__ == "__main__":
    main()
