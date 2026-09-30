"""Log structuré : timestamp | source | sévérité | événement."""
import time
from pathlib import Path


class EventLogger:
    def __init__(self, source="rover", log_dir="logs"):
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        fname = f"{time.strftime('%Y%m%d_%H%M%S')}_{source}.log"
        self._fh = open(Path(log_dir) / fname, "a")
        self.source = source

    def _write(self, severity, event):
        ts = time.time()
        line = (f"[{time.strftime('%H:%M:%S', time.localtime(ts))}.{int(ts*1000)%1000:03d}]"
                f" [{self.source}] [{severity}] {event}")
        self._fh.write(line + "\n")
        self._fh.flush()
        print(line)

    def info(self, event):  self._write("INFO", event)
    def warn(self, event):  self._write("WARNING", event)
    def error(self, event): self._write("ERROR", event)
    def state(self, event): self._write("STATE", event)

    def close(self):
        self._fh.close()