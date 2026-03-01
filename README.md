# How to launch the app on Windows.
Launch script `startup.ps1` to install dependencies.
Launch `run.ps1` to launch the app.


Shared Memory Ring Buffer instead of Queue
Chosen solution: multiprocessing.shared_memory for transferring 4K frames
Rationale:
Zero-copy: A 4K frame (25MB) is not copied between processes; only a pointer to the memory region is passed
Performance: Avoids serialization/deserialization of large numpy arrays via pickle
Memory efficiency: Fixed-size buffer prevents uncontrolled memory growth
Ring buffer pattern: Old frames are automatically overwritten

Frame overproduction issue: With 4 cameras at 15 FPS, Capture produces ~60 frames/sec, while processing at 100ms/frame handles ~10 frames/sec. Solved using FRAME_SUBSAMPLE, storing only selected frames to prevent pipeline overload

Alternative (Queue): Would be slow due to pickle overhead for 25MB frames


Chosen solution: multiprocessing.Queue for transmitting timestamp, frame_id, slot_index
Rationale:
Small size: Metadata (~100 bytes) is efficiently serialized
Thread-safe: Automatic synchronization of access between processes
# TODO Queue for metadata, should be removed and the metadata should be stored in Shared Memory near with frame.
|       ---- HEADER ----       |------ NUMPY ARRAY DATA ------|
| cam_id | slot| ts| frame_num | int64                        |


# IMPORTANT
For a production solution, the optimal approach is to use Linux `tmpfs` for storing frames in RAM. This provides zero-copy access to frames between processes, minimizes disk I/O operations, and ensures high throughput when transferring large 4K data arrays.

In `tmpfs`, its size can be limited and a ring buffer can be implemented at the file system level, preserving the benefits of kernel-space high-speed access and zero-copy.

`mount -t tmpfs -o size=1G tmpfs /mnt/application/cam{0,1,2,3}`
