import numpy as np
from multiprocessing import shared_memory, Value, Semaphore


class RingBuffer:
    def __init__(self, camera_id: str, capacity: int, shape: tuple):
        self.camera_id = camera_id
        self.capacity = capacity
        self.shape = shape
        
        # The size of one frame in bytes
        self.frame_size = np.prod(shape) * np.dtype(np.uint8).itemsize
        total_size = self.capacity * self.frame_size
        
        try:
            self.shm = shared_memory.SharedMemory(name=f"shm_{camera_id}", create=True, size=int(total_size))
        except FileExistsError:
            self.shm = shared_memory.SharedMemory(name=f"shm_{camera_id}")

        self.np_buffer = np.ndarray((capacity, *shape), dtype=np.uint8, buffer=self.shm.buf)
        self.write_idx = 0

        
    def put(self, frame: np.ndarray) -> int:
        idx = self.write_idx
        self.np_buffer[idx][:] = frame
        self.write_idx = (self.write_idx + 1) % self.capacity
        return idx


    def get_frame(self, idx: int):
        return self.np_buffer[idx]


    def close(self):
        self.shm.close()
        self.shm.unlink()
        