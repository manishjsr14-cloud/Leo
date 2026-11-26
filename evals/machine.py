"""The "Machine:" line for check-script report headers.

Reports from the laptop and the gaming desktop must never be mixed up, so each
report says which machine it ran on. The machine is worked out from the GPU name
that nvidia-smi reports, matched against the `machines` section of config.yaml.
No hostname is written: the reports are committed to a public repository.
The line also gives the power state (plugged in or on battery, from psutil),
since a laptop on battery may run slower (M2.3: an unexplained slow hour).
"""

import subprocess

import psutil

from leo.config import load_config

SMI_QUERY = ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"]


# Ask nvidia-smi for "name, total memory" of the first GPU; None if it cannot be run.
def read_gpu() -> str | None:
    try:
        out = subprocess.run(SMI_QUERY, check=False, capture_output=True, text=True,
                             timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = out.stdout.strip().splitlines()
    return lines[0].strip() if out.returncode == 0 and lines else None


# The label whose GPU text appears in the GPU name, or "unknown" when none matches.
def machine_label(gpu: str, machines: dict[str, str]) -> str:
    for label, gpu_text in machines.items():
        if gpu_text.lower() in gpu.lower():
            return label
    return "unknown"


# The power state: "plugged in (battery 100 %)", "on battery (63 %)",
# "no battery reported" (a desktop) or "unknown".
def power_state(battery) -> str:
    if battery is None:
        return "no battery reported"
    if battery.power_plugged is None:
        return "unknown"
    if battery.power_plugged:
        return f"plugged in (battery {battery.percent:.0f} %)"
    return f"on battery ({battery.percent:.0f} %)"


# The header line, e.g. "Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB);
# power: plugged in (battery 100 %)".
def machine_line(gpu_reader=read_gpu, machines: dict[str, str] | None = None,
                 battery_reader=psutil.sensors_battery) -> str:
    machines = load_config().machines if machines is None else machines
    power = f"; power: {power_state(battery_reader())}"
    gpu = gpu_reader()
    if gpu is None:
        return "Machine: unknown (nvidia-smi not found or failed)" + power
    return f"Machine: {machine_label(gpu, machines)} (GPU: {gpu})" + power
