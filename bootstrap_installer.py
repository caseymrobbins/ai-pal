#!/usr/bin/env python3
#
# AI-Pal Self-Contained Bootstrap Installer
#
# This script installs the 'ai-pal' project and its complex dependencies
# by automatically detecting your hardware (OS, GPU, CUDA version) and
# generating a safe, step-by-step installation plan.
#
# It requires Python 3.9+ and 'git' to be installed and on your PATH.
#
# How to run:
# 1. Download this file as 'bootstrap_installer.py'
# 2. Run it from your terminal: python bootstrap_installer.py
#
# This script respects the "Humanity Override" (Gate 3) principle:
# It will show you the full installation plan and ask for your explicit
# permission before running any commands.
#

import sys
import platform
import subprocess
import shutil
import os
import re

# --- Configuration ---
AI_PAL_REPO_URL = "https://github.com/caseymrobbins/ai-pal.git"
PROJECT_DIR_NAME = "ai-pal"
MIN_PYTHON_VERSION = (3, 9)
MIN_DISK_GB = 10
REC_DISK_GB = 16


def check_prerequisites():
    """Checks for Python version and 'git' command."""
    print("--- Checking Prerequisites ---")

    # 1. Check Python Version
    if sys.version_info < MIN_PYTHON_VERSION:
        print(
            f"Error: This installer requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or newer."
        )
        print(f"You are currently running Python {platform.python_version()}")
        sys.exit(1)
    print(f"✅ Python version {platform.python_version()} (OK)")

    # 2. Check for 'git'
    if not shutil.which("git"):
        print("Error: 'git' command not found.")
        print("Please install git and ensure it is in your system's PATH.")
        print("Download from: https://git-scm.com/downloads")
        sys.exit(1)
    print("✅ 'git' command found (OK)")


def get_system_info():
    """
    Gathers hardware and OS info using only the Python standard library.
    This determines which version of PyTorch to install.
    """
    print("\n--- Detecting System Hardware ---")
    info = {
        "os": platform.system(),
        "architecture": platform.machine(),
        "python_exe": sys.executable,  # Path to current python
        "gpu_type": "CPU-Only",  # Default
        "cuda_version": None,
    }

    # 1. Handle Apple Silicon (M-Series)
    if info["os"] == "Darwin" and info["architecture"] == "arm64":
        info["gpu_type"] = "Apple Metal"
        print("Detected Apple Silicon (M-Series) GPU.")

    # 2. Handle NVIDIA (CUDA) and AMD (ROCm)
    elif info["os"] in ["Linux", "Windows"]:
        # Try to find NVIDIA GPU using 'nvidia-smi'
        try:
            # We redirect stderr to devnull to hide "command not found"
            with open(os.devnull, "w") as devnull:
                proc = subprocess.run(
                    ["nvidia-smi"],
                    capture_output=True,
                    text=True,
                    stderr=devnull,
                )
            
            if proc.returncode == 0:
                info["gpu_type"] = "NVIDIA"
                print("Detected NVIDIA GPU.")
                # Parse CUDA version from the output
                for line in proc.stdout.split("\n"):
                    if "CUDA Version" in line:
                        # Line looks like: | CUDA Version: 12.1    Driver Version: ... |
                        match = re.search(r"CUDA Version: ([\d\.]+)", line)
                        if match:
                            info["cuda_version"] = match.group(1)
                            print(f"Detected CUDA Version: {info['cuda_version']}")
                        break
                if not info["cuda_version"]:
                    print("Warning: nvidia-smi found, but could not parse CUDA version.")

            else:
                # 'nvidia-smi' failed or not found, check for AMD 'rocminfo' (Linux-only)
                if info["os"] == "Linux":
                    try:
                        with open(os.devnull, "w") as devnull:
                            proc_rocm = subprocess.run(
                                ["rocminfo"],
                                capture_output=True,
                                text=True,
                                stderr=devnull,
                            )
                        if proc_rocm.returncode == 0 and "gfx" in proc_rocm.stdout:
                            info["gpu_type"] = "AMD ROCm"
                            print("Detected AMD (ROCm) GPU.")
                        else:
                            print("No NVIDIA or AMD GPU found. Defaulting to CPU-Only.")
                    except FileNotFoundError:
                        print("No NVIDIA or AMD GPU found. Defaulting to CPU-Only.")
        
        except FileNotFoundError:
            print("No NVIDIA or AMD GPU tools found. Defaulting to CPU-Only.")
        except Exception as e:
            print(f"Error during GPU detection: {e}. Defaulting to CPU-Only.")

    else:
        print("Unsupported OS for GPU detection. Defaulting to CPU-Only.")

    return info


def check_disk_space(info):
    """Checks for free disk space and warns the user."""
    print("\n--- Checking Disk Space ---")
    try:
        total, used, free = shutil.disk_usage(os.path.abspath(os.curdir))
        free_gb = round(free / (1024**3), 2)
        info["free_disk_gb"] = free_gb

        print(f"Available disk space: {free_gb} GB")
        if free_gb < MIN_DISK_GB:
            print(
                f"\nWarning: This installation requires at least {MIN_DISK_GB} GB."
            )
            print(
                f"({REC_DISK_GB} GB+ is recommended). You are low on space."
            )
            
            try:
                permission = input("Continue anyway? (yes/no): ")
            except EOFError:
                sys.exit(0)
                
            if permission.lower().strip() != "yes":
                print("Installation cancelled.")
                sys.exit(0)
        else:
            print(
                f"✅ Disk space is sufficient ({MIN_DISK_GB} GB required)."
            )

    except Exception as e:
        print(f"Warning: Could not check disk space. ({e})")


def generate_install_plan(info):
    """
    Creates the list of commands to run based on the system info.
    This logic is a direct translation of the 'INSTALL.md' file.
    """
    print("\n--- Generating Installation Plan ---")
    plan = []
    
    # Define platform-specific venv executable paths
    if info["os"] == "Windows":
        venv_pip = os.path.join(".venv", "Scripts", "pip.exe")
        venv_python = os.path.join(".venv", "Scripts", "python.exe")
    else:
        venv_pip = os.path.join(".venv", "bin", "pip")
        venv_python = os.path.join(".venv", "bin", "python")

    # Step 1: Create Virtual Environment
    plan.append({
        "desc": "Create Python virtual environment in ./.venv",
        "cmd": f'"{info["python_exe"]}" -m venv .venv',
    })

    # Step 2: Install PyTorch (The complex part)
    pytorch_cmd = f'"{venv_pip}" install torch'
    pytorch_desc = "Install PyTorch"

    if info["gpu_type"] == "NVIDIA":
        if info["cuda_version"]:
            if info["cuda_version"].startswith("12.1"):
                pytorch_cmd = f'"{venv_pip}" install torch --index-url https://download.pytorch.org/whl/cu121'
                pytorch_desc = "Install PyTorch for CUDA 12.1"
            elif info["cuda_version"].startswith("11.8"):
                pytorch_cmd = f'"{venv_pip}" install torch --index-url https://download.pytorch.org/whl/cu118'
                pytorch_desc = "Install PyTorch for CUDA 11.8"
            else:
                pytorch_desc = (
                    f"Install PyTorch for CUDA {info['cuda_version']} (letting pip choose)"
                )
        else:
            pytorch_desc = (
                "Install PyTorch (NVIDIA GPU detected, but no CUDA version found. Trying default.)"
            )
    
    elif info["gpu_type"] == "Apple Metal":
        pytorch_desc = "Install PyTorch for Apple Metal (M-Series)"
        # Default 'pip install torch' is correct for Metal
    
    elif info["gpu_type"] == "AMD ROCm":
        pytorch_desc = "Install PyTorch for AMD ROCm (Linux-only)"
        # Default 'pip install torch' should pick up ROCm on supported Linux distros
    
    elif info["gpu_type"] == "CPU-Only":
        pytorch_cmd = f'"{venv_pip}" install torch --index-url https://download.pytorch.org/whl/cpu'
        pytorch_desc = "Install PyTorch (CPU-Only)"

    plan.append({"desc": pytorch_desc, "cmd": pytorch_cmd})

    # Step 3: Clone the AI-Pal repository
    plan.append({
        "desc": f"Clone project repository into ./{PROJECT_DIR_NAME}",
        "cmd": f"git clone {AI_PAL_REPO_URL}",
    })

    # Step 4: Install the project and its other dependencies
    plan.append({
        "desc": "Install ai-pal and its dependencies (transformers, spacy, etc.)",
        "cmd": f'"{venv_pip}" install -e {PROJECT_DIR_NAME}',
    })

    # Step 5: Download the spaCy language model
    plan.append({
        "desc": "Download required spaCy model (en_core_web_lg)",
        "cmd": f'"{venv_python}" -m spacy download en_core_web_lg',
    })

    return plan


def execute_plan(plan):
    """
    Displays the plan and asks for user permission to execute it.
    This is the "Humanity Override" (Gate 3).
    """
    print("\n--- 🤖 Installation Plan Ready ---")
    print("This script is ready to run the following commands:")
    print("-" * 35)
    for i, step in enumerate(plan):
        print(f"\n[Step {i + 1}: {step['desc']}]")
        print(f"  $ {step['cmd']}")
    print("\n" + "-" * 35)
    print(f"The project will be installed in a new '{PROJECT_DIR_NAME}' directory.")
    print("A Python virtual environment will be created in ./.venv")

    try:
        permission = input("\nDo you approve and want to execute this plan? (yes/no): ")
    except EOFError:
        print("\nInstallation cancelled.")
        sys.exit(0)

    if permission.lower().strip() != "yes":
        print("Installation cancelled by user.")
        sys.exit(0)

    # --- Start Execution ---
    print("\n--- 🚀 Starting Installation ---")
    for i, step in enumerate(plan):
        print(f"\n--- Running Step {i + 1}: {step['desc']} ---")
        print(f"$ {step['cmd']}\n")
        
        try:
            # Use Popen to stream output in real-time.
            # This is crucial for user feedback during long installs.
            process = subprocess.Popen(
                step['cmd'],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
            )
            
            # Stream the command's stdout
            with process.stdout:
                for line in iter(process.stdout.readline, ""):
                    if not line:
                        break
                    sys.stdout.write(line)
                    sys.stdout.flush()

            process.wait() # Wait for the command to complete

            if process.returncode != 0:
                print(f"\n" + "=" * 50)
                print(f"Error: Step {i + 1} failed with return code {process.returncode}.")
                print("Aborting installation.")
                print("=" * 50)
                sys.exit(1)

        except Exception as e:
            print(f"\n" + "=" * 50)
            print(f"An error occurred while running command: {e}")
            print("Aborting installation.")
            print("=" * 50)
            sys.exit(1)

    print("\n" + ("-" * 50))
    print("✅ AI-Pal installation complete!")
    print("\n--- How to Run ---")
    
    if platform.system() == "Windows":
        print(f"1. Activate the environment: .\\.venv\\Scripts\\activate")
    else:
        print(f"1. Activate the environment: source .venv/bin/activate")
    
    print(f"2. Run the program:         ai-pal")
    print("-" * 50)


def main():
    """Main execution flow of the installer."""
    print("Welcome to the AI-Pal Self-Contained Installer!")
    print("=" * 50)

    try:
        check_prerequisites()
        system_info = get_system_info()
        check_disk_space(system_info)
        
        # Print a summary of detected system
        print("\n--- System Summary ---")
        print(f"  OS:          {system_info['os']} ({system_info['architecture']})")
        print(f"  GPU:         {system_info['gpu_type']}")
        if system_info['cuda_version']:
            print(f"  CUDA:        {system_info['cuda_version']}")
        print(f"  Disk Space:  {system_info.get('free_disk_gb', 'Unknown')} GB Free")
        print("-" * 22)

        install_plan = generate_install_plan(system_info)
        execute_plan(install_plan)

    except KeyboardInterrupt:
        print("\n\nInstallation cancelled by user (Ctrl+C).")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
