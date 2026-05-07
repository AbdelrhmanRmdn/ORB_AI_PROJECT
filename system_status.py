from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
import platform
import shutil
import time


_STARTED_AT = time.time()


@dataclass(frozen=True)
class SystemSnapshot:
    timestamp: str
    uptime_seconds: int
    platform: str
    python_version: str
    cpu_count: int
    load_average: tuple[float, float, float] | None
    memory_total_mb: int | None
    memory_available_mb: int | None
    disk_free_gb: float


def _memory_info() -> tuple[int | None, int | None]:
    try:
        import psutil

        mem = psutil.virtual_memory()
        return int(mem.total / 1024 / 1024), int(mem.available / 1024 / 1024)
    except Exception:
        return None, None


def get_system_status() -> SystemSnapshot:
    total_mem, available_mem = _memory_info()
    disk = shutil.disk_usage("/")
    try:
        load_average = tuple(float(value) for value in os.getloadavg())
    except (AttributeError, OSError):
        load_average = None

    return SystemSnapshot(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        uptime_seconds=int(time.time() - _STARTED_AT),
        platform=f"{platform.system()} {platform.release()} ({platform.machine()})",
        python_version=platform.python_version(),
        cpu_count=os.cpu_count() or 1,
        load_average=load_average,
        memory_total_mb=total_mem,
        memory_available_mb=available_mem,
        disk_free_gb=round(disk.free / 1024 / 1024 / 1024, 2),
    )


def format_system_status() -> str:
    snapshot = get_system_status()
    memory = "memory status unavailable"
    if snapshot.memory_available_mb is not None and snapshot.memory_total_mb is not None:
        memory = (
            f"{snapshot.memory_available_mb} megabytes available out of "
            f"{snapshot.memory_total_mb}"
        )

    load = ""
    if snapshot.load_average:
        load = f", load average {snapshot.load_average[0]:.2f}"

    return (
        f"System online. Uptime is {snapshot.uptime_seconds} seconds, "
        f"{memory}, disk free space is {snapshot.disk_free_gb} gigabytes{load}."
    )
