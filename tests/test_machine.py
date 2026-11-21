"""Tests for evals/machine.py with a fake nvidia-smi reader (no real GPU needed)."""

from evals.machine import machine_line

MACHINES = {"laptop": "GTX 1650", "desktop": "RTX 3060"}


# The laptop's GPU name gives the laptop label.
def test_laptop_gpu_is_labelled_laptop():
    line = machine_line(lambda: "NVIDIA GeForce GTX 1650, 4096 MiB", MACHINES)
    assert line == "Machine: laptop (GPU: NVIDIA GeForce GTX 1650, 4096 MiB)"


# The desktop's GPU name gives the desktop label.
def test_desktop_gpu_is_labelled_desktop():
    line = machine_line(lambda: "NVIDIA GeForce RTX 3060, 12288 MiB", MACHINES)
    assert line == "Machine: desktop (GPU: NVIDIA GeForce RTX 3060, 12288 MiB)"


# A GPU that matches no entry is reported as unknown, never guessed.
def test_other_gpu_is_unknown():
    line = machine_line(lambda: "NVIDIA GeForce RTX 4090, 24564 MiB", MACHINES)
    assert line.startswith("Machine: unknown (GPU: NVIDIA GeForce RTX 4090")


# Without nvidia-smi the line says unknown instead of crashing.
def test_missing_nvidia_smi_is_unknown():
    assert machine_line(lambda: None, MACHINES).startswith("Machine: unknown")
