#!/usr/bin/env python3
"""
Self-Extracting RCC Assistant Launcher

This launcher embeds a complete RCC environment (rcc.exe, .rcc_home, robot project)
as a ZIP payload after a marker. Inspired by Copyparty's self-extracting design.

Usage:
    python assistant.py

On first run:
    - Extracts embedded payload to %LOCALAPPDATA%/MyRccAssistant
    - Sets up ROBOCORP_HOME environment
    - Runs the embedded robot with rcc.exe

Subsequent runs skip extraction if payload already exists.
"""

import os
import sys
import zipfile
import logging
import shutil
import subprocess
import hashlib
from pathlib import Path

# Payload marker - everything after this line is the ZIP payload
PAYLOAD_MARKER = b"===RCC_PAYLOAD_START==="

# Configuration
APP_NAME = "MyRccAssistant"
EXTRACTION_ROOT = None  # Will be set based on OS


def get_extraction_path():
    """Get the extraction directory path based on OS."""
    if sys.platform == "win32":
        # Windows: use %LOCALAPPDATA%
        local_app_data = os.environ.get("LOCALAPPDATA")
        if not local_app_data:
            local_app_data = os.path.expanduser("~\\AppData\\Local")
        return Path(local_app_data) / APP_NAME
    else:
        # Unix-like: use ~/.local/share
        return Path.home() / ".local" / "share" / APP_NAME


def setup_logging(log_dir):
    """Configure logging to both file and console."""
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "launcher.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def find_payload_offset(script_path):
    """
    Find the byte offset where the ZIP payload starts.
    Returns the offset or None if marker not found.
    
    Note: Searches for the LAST occurrence of the marker, since the marker
    constant is defined in the launcher source code itself.
    """
    with open(script_path, "rb") as f:
        content = f.read()
    
    # Find the LAST occurrence of the marker (rfind)
    marker_pos = content.rfind(PAYLOAD_MARKER)
    if marker_pos == -1:
        return None
    
    # Payload starts right after the marker
    return marker_pos + len(PAYLOAD_MARKER)


def calculate_payload_hash(script_path, offset):
    """Calculate SHA256 hash of the embedded payload."""
    hasher = hashlib.sha256()
    with open(script_path, "rb") as f:
        f.seek(offset)
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def extract_payload(script_path, offset, target_dir, logger):
    """
    Extract the embedded ZIP payload to target directory.
    
    Args:
        script_path: Path to this script file
        offset: Byte offset where ZIP payload starts
        target_dir: Directory to extract payload into
        logger: Logger instance
    """
    logger.info(f"Extracting payload to: {target_dir}")
    
    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract ZIP payload
    temp_zip = target_dir / ".temp_payload.zip"
    try:
        # Copy payload to temporary ZIP file
        with open(script_path, "rb") as src:
            src.seek(offset)
            with open(temp_zip, "wb") as dst:
                shutil.copyfileobj(src, dst)
        
        # Extract ZIP contents
        logger.info("Extracting ZIP contents...")
        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            zip_ref.extractall(target_dir)
        
        logger.info(f"Extraction complete: {len(list(target_dir.rglob('*')))} items extracted")
        
    finally:
        # Clean up temporary ZIP file
        if temp_zip.exists():
            temp_zip.unlink()


def should_extract(target_dir, script_path, offset, logger):
    """
    Determine if extraction is needed.
    
    Returns True if:
    - Target directory doesn't exist
    - Target directory is empty
    - Payload hash has changed (indicates updated bundle)
    """
    if not target_dir.exists():
        logger.info("Target directory does not exist, extraction needed")
        return True
    
    # Check if directory is empty
    if not any(target_dir.iterdir()):
        logger.info("Target directory is empty, extraction needed")
        return True
    
    # Check payload hash
    hash_file = target_dir / ".payload_hash"
    if not hash_file.exists():
        logger.info("Payload hash file missing, extraction needed")
        return True
    
    current_hash = calculate_payload_hash(script_path, offset)
    stored_hash = hash_file.read_text().strip()
    
    if current_hash != stored_hash:
        logger.info("Payload hash changed, re-extraction needed")
        logger.info(f"  Stored: {stored_hash}")
        logger.info(f"  Current: {current_hash}")
        return True
    
    logger.info("Payload unchanged, skipping extraction")
    return False


def save_payload_hash(target_dir, script_path, offset):
    """Save the current payload hash for future comparison."""
    current_hash = calculate_payload_hash(script_path, offset)
    hash_file = target_dir / ".payload_hash"
    hash_file.write_text(current_hash)


def find_rcc_executable(target_dir):
    """Find rcc.exe or rcc in the extracted payload."""
    # Check common locations
    candidates = [
        target_dir / "rcc.exe",
        target_dir / "rcc",
        target_dir / "bin" / "rcc.exe",
        target_dir / "bin" / "rcc",
    ]
    
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    
    # Search recursively
    for rcc_path in target_dir.rglob("rcc*"):
        if rcc_path.is_file() and (rcc_path.name == "rcc.exe" or rcc_path.name == "rcc"):
            return rcc_path
    
    return None


def find_robot_yaml(target_dir):
    """Find robot.yaml in the extracted payload."""
    # Check common locations
    candidates = [
        target_dir / "robot" / "robot.yaml",
        target_dir / "robot.yaml",
        target_dir / "assistant" / "robot.yaml",
    ]
    
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    
    # Search recursively
    for robot_path in target_dir.rglob("robot.yaml"):
        return robot_path
    
    return None


def find_rcc_home(target_dir):
    """Find .rcc_home directory in the extracted payload."""
    candidates = [
        target_dir / ".rcc_home",
        target_dir / "rcc_home",
    ]
    
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    
    return None


def run_rcc(rcc_exe, robot_yaml, rcc_home, logger):
    """
    Execute RCC with the embedded robot.
    
    Args:
        rcc_exe: Path to rcc executable
        robot_yaml: Path to robot.yaml
        rcc_home: Path to .rcc_home directory (optional)
        logger: Logger instance
    """
    logger.info(f"Running RCC: {rcc_exe}")
    logger.info(f"Robot: {robot_yaml}")
    
    # Build command
    cmd = [str(rcc_exe), "run", "--robot", str(robot_yaml)]
    
    # Set up environment
    env = os.environ.copy()
    
    if rcc_home:
        logger.info(f"Using ROBOCORP_HOME: {rcc_home}")
        env["ROBOCORP_HOME"] = str(rcc_home)
    
    # Run RCC
    logger.info(f"Executing command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            env=env,
            cwd=robot_yaml.parent,
            capture_output=False,  # Stream output directly
            text=True
        )
        
        if result.returncode != 0:
            logger.error(f"RCC exited with code {result.returncode}")
            return result.returncode
        
        logger.info("RCC execution completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Failed to execute RCC: {e}")
        return 1


def main():
    """Main launcher entry point."""
    script_path = Path(__file__).resolve()
    
    # Get extraction directory
    extraction_dir = get_extraction_path()
    
    # Setup logging
    logger = setup_logging(extraction_dir)
    logger.info("=" * 60)
    logger.info("RCC Self-Extracting Assistant Launcher")
    logger.info("=" * 60)
    logger.info(f"Script: {script_path}")
    logger.info(f"Target: {extraction_dir}")
    
    # Find payload
    logger.info("Searching for embedded payload...")
    offset = find_payload_offset(script_path)
    
    if offset is None:
        logger.error("No embedded payload found!")
        logger.error("This script must be built with builder.py to include the RCC payload.")
        logger.error("Marker expected: ===RCC_PAYLOAD_START===")
        return 1
    
    logger.info(f"Payload found at offset: {offset} bytes")
    
    # Extract if needed
    if should_extract(extraction_dir, script_path, offset, logger):
        try:
            extract_payload(script_path, offset, extraction_dir, logger)
            save_payload_hash(extraction_dir, script_path, offset)
        except Exception as e:
            logger.error(f"Extraction failed: {e}", exc_info=True)
            return 1
    
    # Find RCC executable
    logger.info("Locating RCC executable...")
    rcc_exe = find_rcc_executable(extraction_dir)
    if not rcc_exe:
        logger.error("Could not find rcc.exe in extracted payload")
        return 1
    logger.info(f"Found RCC: {rcc_exe}")
    
    # Find robot.yaml
    logger.info("Locating robot.yaml...")
    robot_yaml = find_robot_yaml(extraction_dir)
    if not robot_yaml:
        logger.error("Could not find robot.yaml in extracted payload")
        return 1
    logger.info(f"Found robot: {robot_yaml}")
    
    # Find .rcc_home (optional)
    rcc_home = find_rcc_home(extraction_dir)
    if rcc_home:
        logger.info(f"Found RCC home: {rcc_home}")
    else:
        logger.warning("No .rcc_home directory found, RCC will use default")
    
    # Run RCC
    return run_rcc(rcc_exe, robot_yaml, rcc_home, logger)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
