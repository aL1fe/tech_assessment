import time
import threading
from multiprocessing import Queue

from fake_camera import FakeCamera, CameraError
from config import settings
from shared_ring_buffer import CameraBuffer


def main():
    metadata_queue = Queue()

    def camera_worker(camera_id: str, fps: int, metadata_queue: Queue):
        buffer = CameraBuffer(camera_id, capacity=10, shape=(settings.HEIGHT, settings.WIDTH, settings.CHANNELS))
        retries = 0
        try:
            while True:
                start_time = time.monotonic()
                try:
                    cam = FakeCamera(camera_id=camera_id, fps=fps)
                    print(f"[{camera_id}] Connected")
                    while True:
                        frame = cam.read()
                        # Save every x frame to prevent overload Porcessing service
                        if cam.frame_count % 100 == 0:  # TODO move '6' to settings
                            slot_idx = buffer.put(frame)

                            metadata_queue.put({
                                "cam_id": camera_id,
                                "slot": slot_idx,
                                "ts": time.time(),
                                "frame_num": cam.frame_count
                            })
                            print(f"[{camera_id}] Current queue size: {metadata_queue.qsize()}")
                            print(f"[{cam.camera_id}] frame {cam.frame_count}, size={frame.nbytes / 1024 / 1024:.1f} MB")

                except CameraError as e:
                    uptime = time.monotonic() - start_time
                    print(f"[{camera_id}] Disconnected after {uptime:.1f}s: {e}")

                    retries = 0 if uptime >= settings.STABLE_THRESHOLD else retries + 1

                    delay = min(settings.MAX_DELAY, settings.BASE_DELAY * 2 ** retries)
                    print(f"[{camera_id}] Reconnect in {delay:.1f}s")

                    time.sleep(delay)

                except Exception as e:
                    print(f"Critical error in thread {camera_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    break

        finally:
                buffer.close()

    for key, cfg in settings.CAMERA_CFG.items():
        t = threading.Thread(target=camera_worker, args=(key, cfg.fps, metadata_queue), daemon=True)
        t.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("[Main] Stopping...")
       

if __name__ == "__main__":
    main()
