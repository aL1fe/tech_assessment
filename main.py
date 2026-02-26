import time
import threading
from fake_camera import FakeCamera, CameraError

from config import settings, CameraConfig

def main():
    def camera_worker(camera_id: str, fps: int):
        retries = 0
        while True:
            start_time = time.monotonic()
            try:
                cam = FakeCamera(camera_id=camera_id, fps=fps)
                print(f"[{camera_id}] Connected")
                while True:
                    frame = cam.read()
                    if cam.frame_count % 6 == 0:  # TODO move 6 to settings
                        pass  # Save every x frame to prevent overload Porcessing service

                    # Print every 100th frame
                    if cam.frame_count % 100 == 0:
                        print(f"[{cam.camera_id}] frame {cam.frame_count}, shape={frame.shape}, "
                            f"size={frame.nbytes / 1024 / 1024:.1f} MB")
            except CameraError as e:
                uptime = 0
                if start_time:
                    uptime = time.monotonic() - start_time
                print(f"[{camera_id}] Disconnected after {uptime:.1f}s: {e}")

                if uptime >= settings.STABLE_THRESHOLD:
                    retries = 0  # Connection was stable. Reset retries
                    print(f"[{camera_id}] Connection was stable. Reset retries.")
                else:
                    retries += 1

                delay = min(settings.MAX_DELAY, settings.BASE_DELAY * 2 ** retries)
                print(f"[{camera_id}] Reconnect in {delay:.1f}s")

                time.sleep(delay)

    # Init cameras add shared mem
    for key, cfg in settings.CAMERA_CFG.items():
        t = threading.Thread(target=camera_worker, args=(key, cfg.fps), daemon=True)
        t.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("[Main] Stopping...")
       

if __name__ == "__main__":
    main()
