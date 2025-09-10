from pathlib import Path

from app.capture.buffer import RollingBuffer


def test_buffer_drops_oldest_and_retains_duration():
    fps = 5
    seconds = 2
    buffer = RollingBuffer(fps=fps, seconds=seconds)

    # simulate timestamps at 0.2s intervals
    for i in range(15):
        ts = i * 0.2
        buffer.append(Path(f"frame_{i}.jpg"), ts)

    items = buffer.to_list()
    assert len(items) == fps * seconds
    # Oldest frame should be frame_5
    assert items[0].path.name == "frame_5.jpg"

    # The buffer should cover roughly the configured duration
    duration = items[-1].ts - items[0].ts
    assert duration <= seconds
    assert duration >= seconds - (1 / fps)
