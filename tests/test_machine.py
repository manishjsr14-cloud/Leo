"""Tests for evals/machine.py with a fake nvidia-smi reader (no real GPU needed)."""

from types import SimpleNamespace

from evals.machine import machine_line, power_state

MACHINES = {"laptop": "GTX 1650", "desktop": "RTX 3060"}
PLUGGED = SimpleNamespace(percent=100, power_plugged=True)


# machine_line with a fixed GPU and battery (plugged in unless given).
def line_for(gpu, battery=PLUGGED) -> str:
    return machine_line(lambda: gpu, MACHINES, lambda: battery)


# The laptop's GPU name gives the laptop label.
def test_laptop_gpu_is_labelled_laptop():
    line = line_for("NVIDIA GeForce GTX 1650, 4096 MiB")
    assert line == ("Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB); "
                    "power: plugged in (battery 100 %)")


# The desktop's GPU name gives the desktop label.
def test_desktop_gpu_is_labelled_desktop():
    line = line_for("NVIDIA GeForce RTX 3060, 12288 MiB", battery=None)
    assert line == ("Machine: desktop (GPU: NVIDIA GeForce RTX 3060, 12288 MiB); "
                    "power: no battery reported")


# A GPU that matches no entry is reported as unknown, never guessed.
def test_other_gpu_is_unknown():
    line = line_for("NVIDIA GeForce RTX 4090, 24564 MiB")
    assert line.startswith("Machine: unknown (GPU: NVIDIA GeForce RTX 4090")


# Without nvidia-smi the line says unknown instead of crashing.
def test_missing_nvidia_smi_is_unknown():
    assert line_for(None).startswith("Machine: unknown")


# Power state: plugged in, on battery, no battery, unknown.
def test_power_state():
    assert power_state(PLUGGED) == "plugged in (battery 100 %)"
    assert power_state(SimpleNamespace(percent=62.6, power_plugged=False)) == "on battery (63 %)"
    assert power_state(None) == "no battery reported"
    assert power_state(SimpleNamespace(percent=50, power_plugged=None)) == "unknown"
