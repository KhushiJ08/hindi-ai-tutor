"""
Prajna — Automatic Hardware Detection & Model Setup
====================================================
This script runs BEFORE the server starts. It:
  1. Detects the system's total RAM (cross-platform)
  2. Selects the best Gemma 4 model variant
  3. Pulls the model via Ollama (if not already cached)
  4. Writes the model name to .prajna_model for the server to read

Exit codes:
  0 = success (model is ready)
  1 = failure (hardware too weak or Ollama not available)
"""

import os
import platform
import subprocess
import sys


def get_total_ram_gb():
    """Detect total system RAM in GB. Works on Linux, macOS, and Windows."""
    system = platform.system()

    try:
        if system == "Linux":
            with open("/proc/meminfo", "r") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        # MemTotal is in kB
                        kb = int(line.split()[1])
                        return kb / (1024 * 1024)

        elif system == "Darwin":  # macOS
            result = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return int(result.stdout.strip()) / (1024 ** 3)

        elif system == "Windows":
            result = subprocess.run(
                ["wmic", "os", "get", "TotalVisibleMemorySize"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    line = line.strip()
                    if line.isdigit():
                        return int(line) / (1024 * 1024)

    except Exception as e:
        print(f"  [!] RAM detection error: {e}")

    return None


def select_model(ram_gb):
    """Choose the best model based on available RAM.

    Returns:
        str or None — model name, or None if hardware is too weak.
    """
    if ram_gb >= 7.5:
        return "gemma4:e4b"
    elif ram_gb >= 3.5:
        return "gemma4:e2b"
    else:
        return None  # Hardware too weak


def is_model_cached(model_name):
    """Check if the model is already downloaded in Ollama."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode == 0:
            return model_name in result.stdout
    except Exception:
        pass
    return False


def pull_model(model_name):
    """Pull the model using Ollama. Shows progress in the terminal."""
    print(f"  Pulling {model_name} (first time setup — this may take a while)...")
    print(f"  Do NOT close this window.\n")
    try:
        # Use subprocess.call so the download progress bar is visible
        exit_code = subprocess.call(["ollama", "pull", model_name], timeout=3600)
        return exit_code == 0
    except subprocess.TimeoutExpired:
        print("  [!] Download timed out after 1 hour.")
        return False
    except FileNotFoundError:
        print("  [!] 'ollama' command not found. Please install Ollama first:")
        print("      https://ollama.com/download")
        return False
    except Exception as e:
        print(f"  [!] Failed to pull model: {e}")
        return False


def main():
    print("=" * 50)
    print("  Prajna — Hardware Auto-Detection")
    print("=" * 50)
    print()

    # Step 1: Detect RAM
    ram_gb = get_total_ram_gb()

    if ram_gb is None:
        print("  [!] Could not detect system RAM.")
        print("  Defaulting to balanced model: gemma4:e2b")
        model = "gemma4:e2b"
        ram_gb = 0  # for display
    else:
        print(f"  Detected RAM: {ram_gb:.1f} GB")
        print()

        # Step 2: Select model
        model = select_model(ram_gb)

        if model is None:
            print("  " + "=" * 46)
            print("  [ERROR] Your device does not have enough RAM")
            print(f"  to run Prajna (detected {ram_gb:.1f} GB).")
            print()
            print("  Minimum requirement: 4 GB RAM")
            print()
            print("  Options:")
            print("    1. Run Prajna on a computer with more RAM")
            print("    2. Close other applications to free memory")
            print("    3. Ask a friend with a stronger laptop")
            print("  " + "=" * 46)
            sys.exit(1)

    # Step 3: Report selection
    if ram_gb >= 7.5:
        print(f"  [*] Selecting HIGH-QUALITY model: {model}")
        print(f"      Best experience — detailed Hindi explanations")
    else:
        print(f"  [*] Selecting BALANCED model: {model}")
        print(f"      Good quality — optimized for your hardware")
    print()

    # Step 4: Pull model if needed
    if is_model_cached(model):
        print(f"  [OK] {model} is already downloaded. Skipping pull.")
    else:
        success = pull_model(model)
        if not success:
            print(f"\n  [!] Failed to download {model}.")
            print(f"  Please check your internet connection and try again.")
            sys.exit(1)

    # Step 5: Write model choice to file for the server to read
    model_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".prajna_model")
    with open(model_file, "w") as f:
        f.write(model)

    print()
    print(f"  [OK] Model ready: {model}")
    print(f"  [OK] Saved to .prajna_model")
    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
