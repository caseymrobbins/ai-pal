"""Hardware detection and optimization."""

import platform
import psutil
import torch
from dataclasses import dataclass
from typing import Optional, Literal
from loguru import logger

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

try:
    import pynvml
    PYNVML_AVAILABLE = True
except ImportError:
    PYNVML_AVAILABLE = False


@dataclass
class HardwareInfo:
    """Hardware information."""

    # CPU
    cpu_count: int
    cpu_freq_max: float  # MHz
    ram_total_gb: float
    ram_available_gb: float

    # GPU
    has_gpu: bool
    gpu_name: Optional[str] = None
    gpu_vram_total_gb: Optional[float] = None
    gpu_vram_available_gb: Optional[float] = None
    gpu_count: int = 0

    # Platform
    platform: str = ""
    python_version: str = ""

    # Compute backend
    compute_backend: Literal["cuda", "mps", "cpu"] = "cpu"

    def __str__(self) -> str:
        """String representation."""
        lines = [
            f"Platform: {self.platform}",
            f"Python: {self.python_version}",
            f"CPU: {self.cpu_count} cores @ {self.cpu_freq_max:.0f} MHz",
            f"RAM: {self.ram_available_gb:.1f}GB / {self.ram_total_gb:.1f}GB available",
        ]

        if self.has_gpu:
            lines.append(f"GPU: {self.gpu_name}")
            lines.append(
                f"VRAM: {self.gpu_vram_available_gb:.1f}GB / "
                f"{self.gpu_vram_total_gb:.1f}GB available"
            )
            lines.append(f"Compute Backend: {self.compute_backend.upper()}")
        else:
            lines.append("GPU: None detected (using CPU)")

        return "\n".join(lines)


class HardwareDetector:
    """Detects and reports hardware capabilities."""

    @staticmethod
    def detect() -> HardwareInfo:
        """Detect hardware capabilities."""
        logger.info("Detecting hardware capabilities...")

        # CPU & RAM
        cpu_count = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_max = cpu_freq.max if cpu_freq else 0.0

        ram = psutil.virtual_memory()
        ram_total_gb = ram.total / (1024**3)
        ram_available_gb = ram.available / (1024**3)

        # Platform
        platform_str = f"{platform.system()} {platform.release()}"
        python_version = platform.python_version()

        # GPU Detection
        has_gpu = False
        gpu_name = None
        gpu_vram_total_gb = None
        gpu_vram_available_gb = None
        gpu_count = 0
        compute_backend = "cpu"

        # Check CUDA (NVIDIA)
        if torch.cuda.is_available():
            has_gpu = True
            compute_backend = "cuda"
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0)

            if PYNVML_AVAILABLE:
                try:
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    gpu_vram_total_gb = mem_info.total / (1024**3)
                    gpu_vram_available_gb = mem_info.free / (1024**3)
                    pynvml.nvmlShutdown()
                except Exception as e:
                    logger.warning(f"Failed to get detailed GPU info: {e}")

            if not gpu_vram_total_gb and GPUTIL_AVAILABLE:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus:
                        gpu = gpus[0]
                        gpu_vram_total_gb = gpu.memoryTotal / 1024
                        gpu_vram_available_gb = gpu.memoryFree / 1024
                except Exception as e:
                    logger.warning(f"Failed to get GPU info via GPUtil: {e}")

        # Check MPS (Apple Silicon)
        elif torch.backends.mps.is_available():
            has_gpu = True
            compute_backend = "mps"
            gpu_count = 1
            gpu_name = "Apple Silicon (MPS)"
            # MPS doesn't expose VRAM details easily
            # Use system RAM as approximation
            gpu_vram_total_gb = ram_total_gb
            gpu_vram_available_gb = ram_available_gb

        # Check ROCm (AMD)
        elif hasattr(torch.version, "hip") and torch.version.hip is not None:
            has_gpu = True
            compute_backend = "cuda"  # ROCm uses CUDA-compatible API
            gpu_count = torch.cuda.device_count()
            gpu_name = "AMD GPU (ROCm)"

        info = HardwareInfo(
            cpu_count=cpu_count,
            cpu_freq_max=cpu_freq_max,
            ram_total_gb=ram_total_gb,
            ram_available_gb=ram_available_gb,
            has_gpu=has_gpu,
            gpu_name=gpu_name,
            gpu_vram_total_gb=gpu_vram_total_gb,
            gpu_vram_available_gb=gpu_vram_available_gb,
            gpu_count=gpu_count,
            platform=platform_str,
            python_version=python_version,
            compute_backend=compute_backend,
        )

        logger.info(f"Hardware detected:\n{info}")
        return info

    @staticmethod
    def recommend_model_size(hardware: HardwareInfo) -> str:
        """Recommend optimal model size based on hardware."""
        if not hardware.has_gpu:
            # CPU only - recommend smaller models
            if hardware.ram_available_gb >= 16:
                return "7B"  # 7 billion parameters
            elif hardware.ram_available_gb >= 8:
                return "3B"
            else:
                return "1B"

        # GPU available
        vram_gb = hardware.gpu_vram_available_gb or 0

        if vram_gb >= 40:
            return "70B"  # Can run large models
        elif vram_gb >= 24:
            return "34B"
        elif vram_gb >= 16:
            return "13B"
        elif vram_gb >= 8:
            return "7B"
        elif vram_gb >= 4:
            return "3B"
        else:
            return "1B"

    @staticmethod
    def get_torch_device() -> torch.device:
        """Get the optimal PyTorch device."""
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")

    @staticmethod
    def get_device_map(model_size: str = "7B") -> str:
        """Get device map strategy for model loading."""
        hardware = HardwareDetector.detect()

        if not hardware.has_gpu:
            return "cpu"

        # For GPU, use auto device mapping
        return "auto"


# Global hardware info
_hardware_info: Optional[HardwareInfo] = None


def get_hardware_info() -> HardwareInfo:
    """Get cached hardware information."""
    global _hardware_info
    if _hardware_info is None:
        _hardware_info = HardwareDetector.detect()
    return _hardware_info
