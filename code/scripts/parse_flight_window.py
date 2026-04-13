import re
from pathlib import Path

def parse_flight_window_from_extract_log(log_path: Path, margin_s: float ) -> tuple[float, float]:
    """Parse Event 1 start/stop times from extract_Mission 1.log.
    Returns (start_time, stop_time) with margin added for IMU initialization.
    """
    pattern = re.compile(r"Event\s+1\s+\d+\s+(\d+\.\d+)\s+(\d+\.\d+)")
    text = log_path.read_text()
    match = pattern.search(text)
    if not match:
        raise ValueError(f"No Event 1 found in {log_path}")
    return float(match.group(1)) - margin_s, float(match.group(2)) + margin_s


if __name__ == "__main__":
    log_file = Path("E:/mjolnir_processing/re112o_250610/tmp/importapx/Mission 1/Extract/extract_Mission 1.log")
    start, stop = parse_flight_window_from_extract_log(log_path =log_file, margin_s = 200.0)
    print(f"Parsed flight window: {start} - {stop} (with margin)")