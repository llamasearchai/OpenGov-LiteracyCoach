from typing import List


def estimate_speaking_duration_timestamps(timestamps: List[float]) -> float:
    if not timestamps or len(timestamps) < 2:
        return 60.0
    start = min(timestamps)
    end = max(timestamps)
    return max(0.001, end - start)


def tokens(text: str) -> List[str]:
    return [token for token in text.strip().split() if token]


