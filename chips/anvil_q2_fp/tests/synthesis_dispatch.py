"""Bound native synthesis concurrency by current CPU and memory headroom.

The retained four-job preparation measurement observed a maximum individual
RSS of 1,369,852 KiB. Reserve 2 GiB per job and leave at least 1 GiB and one
quarter of available memory unused. This changes scheduling, never coverage.
"""

import math
import os
from pathlib import Path


GIB = 1024 ** 3
JOB_MEMORY_BYTES = 2 * GIB
MAXIMUM_JOBS = 4


def resources():
    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        fields = dict(line.split(":", 1) for line in meminfo.read_text().splitlines())
        available = int(fields["MemAvailable"].split()[0]) * 1024
        memory_method = "MemAvailable"
    else:
        available = os.sysconf("SC_AVPHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        memory_method = "SC_AVPHYS_PAGES"
    cpus = (len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity")
            else os.cpu_count())
    if cpus is None or cpus < 1:
        raise RuntimeError("cannot determine CPU capacity for bounded synthesis dispatch")
    limits = []
    membership = Path("/proc/self/cgroup")
    if membership.is_file():
        for line in membership.read_text().splitlines():
            hierarchy, controllers, group = line.split(":", 2)
            if hierarchy == "0" and not controllers:
                root = Path("/sys/fs/cgroup")
                directory = root / group.lstrip("/")
                while True:
                    maximum = directory / "memory.max"
                    if maximum.is_file():
                        limit = maximum.read_text().strip()
                        if limit != "max":
                            current = int((directory / "memory.current").read_text())
                            remaining = max(0, int(limit) - current)
                            available = min(available, remaining)
                            limits.append(dict(kind="memory", maximum_bytes=int(limit),
                                               current_bytes=current))
                    quota_path = directory / "cpu.max"
                    if quota_path.is_file():
                        quota, period = quota_path.read_text().split()
                        if quota != "max":
                            capacity = int(quota) / int(period)
                            cpus = min(cpus, max(1, math.floor(capacity)))
                            limits.append(dict(kind="cpu", capacity=capacity))
                    if directory == root:
                        break
                    directory = directory.parent
            elif "memory" in controllers.split(","):
                directory = Path("/sys/fs/cgroup/memory") / group.lstrip("/")
                maximum = directory / "memory.limit_in_bytes"
                if maximum.is_file():
                    limit = int(maximum.read_text())
                    current = int((directory / "memory.usage_in_bytes").read_text())
                    available = min(available, max(0, limit - current))
                    limits.append(dict(kind="memory-v1", maximum_bytes=limit,
                                       current_bytes=current))
    return dict(available_bytes=available, cpu_capacity=cpus,
                memory_method=memory_method, cgroup_limits=limits)


def policy(snapshot):
    headroom = max(GIB, snapshot["available_bytes"] // 4)
    budget = max(0, snapshot["available_bytes"] - headroom)
    workers = min(MAXIMUM_JOBS, snapshot["cpu_capacity"], budget // JOB_MEMORY_BYTES)
    if workers < 1:
        raise RuntimeError(
            "insufficient available memory for native synthesis: "
            f"{snapshot['available_bytes']} bytes available, "
            f"{JOB_MEMORY_BYTES} bytes/job plus {headroom} bytes headroom required")
    return dict(snapshot, maximum_concurrent_jobs=workers,
                per_job_reserved_bytes=JOB_MEMORY_BYTES, headroom_bytes=headroom)
