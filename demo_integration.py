#!/usr/bin/env python3
"""
Complete End-to-End Demonstration of fetch-repos-bot Integration

This script demonstrates the full process:
1. Download RCC
2. Clone fetch-repos-bot
3. Pre-build Holotree environment
4. Create payload.zip with embedded environment
5. Build self-extracting assistant.py
6. Verify the binary contains the full launcher + payload
"""

import os
import sys
import subprocess
import tempfile
import shutil
import zipfile
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def download_rcc(target_dir):
    """Download RCC executable."""
    logger.info("=" * 70)
    logger.info("STEP 1: Downloading RCC")
    logger.info("=" * 70)
    
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    
    if sys.platform == "win32":
        rcc_url = "https://downloads.robocorp.com/rcc/releases/latest/windows64/rcc.exe"
        rcc_name = "rcc.exe"
    elif sys.platform == "darwin":
        rcc_url = "https://downloads.robocorp.com/rcc/releases/latest/macos64/rcc"
        rcc_name = "rcc"
    else:
        rcc_url = "https://downloads.robocorp.com/rcc/releases/latest/linux64/rcc"
        rcc_name = "rcc"
    
    rcc_path = target_dir / rcc_name
    
    logger.info(f"Downloading from: {rcc_url}")
    logger.info(f"Saving to: {rcc_path}")
    
    result = subprocess.run(
        ["curl", "-L", "-o", str(rcc_path), rcc_url],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to download RCC: {result.stderr}")
        return None
    
    # Make executable
    os.chmod(rcc_path, 0o755)
    
    # Verify
    result = subprocess.run(
        [str(rcc_path), "version"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        logger.info(f"✓ RCC downloaded successfully")
        logger.info(f"  Version info: {result.stdout.strip()[:100]}")
        return rcc_path
    else:
        logger.error(f"RCC download verification failed: {result.stderr}")
        return None


def clone_fetch_repos_bot(target_dir):
    """Clone the fetch-repos-bot repository."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 2: Cloning fetch-repos-bot")
    logger.info("=" * 70)
    
    target_dir = Path(target_dir)
    repo_url = "https://github.com/joshyorko/fetch-repos-bot"
    
    logger.info(f"Cloning from: {repo_url}")
    logger.info(f"Target: {target_dir}")
    
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        logger.error(f"Failed to clone: {result.stderr}")
        return False
    
    # Verify robot.yaml exists
    robot_yaml = target_dir / "robot.yaml"
    if not robot_yaml.exists():
        logger.error(f"robot.yaml not found in {target_dir}")
        return False
    
    logger.info(f"✓ fetch-repos-bot cloned successfully")
    logger.info(f"✓ Found robot.yaml at: {robot_yaml}")
    
    return True


def prebuild_holotree(rcc_path, robot_dir, rcc_home_dir):
    """Pre-build the Holotree environment."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 3: Pre-building Holotree Environment")
    logger.info("=" * 70)
    
    rcc_path = Path(rcc_path)
    robot_dir = Path(robot_dir)
    rcc_home_dir = Path(rcc_home_dir)
    robot_yaml = robot_dir / "robot.yaml"
    
    # Create RCC home directory
    rcc_home_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"RCC: {rcc_path}")
    logger.info(f"Robot: {robot_yaml}")
    logger.info(f"ROBOCORP_HOME: {rcc_home_dir}")
    
    # Set environment
    env = os.environ.copy()
    env["ROBOCORP_HOME"] = str(rcc_home_dir.resolve())
    
    logger.info("")
    logger.info("Building Holotree (this may take a few minutes)...")
    
    # Use holotree variables to materialize the environment
    result = subprocess.run(
        [str(rcc_path), "holotree", "variables", str(robot_yaml)],
        env=env,
        capture_output=True,
        text=True,
        timeout=300  # 5 minute timeout
    )
    
    if result.returncode != 0:
        logger.warning(f"Holotree build had non-zero exit: {result.returncode}")
        logger.warning(f"Output: {result.stdout}")
        logger.warning(f"Errors: {result.stderr}")
    else:
        logger.info(f"✓ Holotree command executed")
    
    # Check if Holotree was created
    if rcc_home_dir.exists() and any(rcc_home_dir.iterdir()):
        files = list(rcc_home_dir.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        dir_count = len([f for f in files if f.is_dir()])
        
        logger.info(f"✓ Holotree created at: {rcc_home_dir}")
        logger.info(f"  Files: {file_count}")
        logger.info(f"  Directories: {dir_count}")
        
        # Calculate size
        total_size = sum(f.stat().st_size for f in files if f.is_file())
        logger.info(f"  Total size: {total_size / 1024 / 1024:.2f} MB")
        
        return True
    else:
        logger.error("✗ Holotree directory is empty or not created")
        return False


def create_payload_with_embedded_holotree(rcc_path, rcc_home_dir, robot_dir, output_zip):
    """Create payload.zip with RCC, Holotree, and robot."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 4: Creating Payload ZIP")
    logger.info("=" * 70)
    
    rcc_path = Path(rcc_path)
    rcc_home_dir = Path(rcc_home_dir)
    robot_dir = Path(robot_dir)
    output_zip = Path(output_zip)
    
    logger.info(f"Creating: {output_zip}")
    
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add RCC executable
        logger.info(f"Adding RCC: {rcc_path.name}")
        zf.write(rcc_path, rcc_path.name)
        
        # Add .rcc_home (pre-built Holotree)
        logger.info(f"Adding Holotree: {rcc_home_dir}")
        file_count = 0
        for file_path in rcc_home_dir.rglob("*"):
            if file_path.is_file():
                arcname = Path(".rcc_home") / file_path.relative_to(rcc_home_dir)
                zf.write(file_path, arcname)
                file_count += 1
                if file_count % 100 == 0:
                    logger.info(f"  Added {file_count} Holotree files...")
        
        logger.info(f"✓ Added {file_count} Holotree files")
        
        # Add robot project
        logger.info(f"Adding robot: {robot_dir}")
        robot_file_count = 0
        for file_path in robot_dir.rglob("*"):
            if file_path.is_file():
                # Skip .git and other hidden files
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if "__pycache__" in file_path.parts:
                    continue
                
                arcname = Path("robot") / file_path.relative_to(robot_dir)
                zf.write(file_path, arcname)
                robot_file_count += 1
        
        logger.info(f"✓ Added {robot_file_count} robot files")
        
        total_files = len(zf.namelist())
        logger.info(f"✓ Payload ZIP created: {total_files} total files")
    
    # Check size
    zip_size = output_zip.stat().st_size
    logger.info(f"✓ Payload size: {zip_size / 1024 / 1024:.2f} MB")
    
    return True


def build_self_extracting_assistant(payload_zip, output_file):
    """Build the self-extracting assistant.py."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 5: Building Self-Extracting Assistant")
    logger.info("=" * 70)
    
    # Import builder module
    sys.path.insert(0, str(Path(__file__).parent))
    import builder
    
    launcher_path = Path(__file__).parent / "launcher.py"
    payload_zip = Path(payload_zip)
    output_file = Path(output_file)
    
    logger.info(f"Launcher: {launcher_path}")
    logger.info(f"Payload: {payload_zip}")
    logger.info(f"Output: {output_file}")
    
    # Build
    builder.create_self_extracting_file(
        launcher_path,
        payload_zip,
        output_file,
        logger
    )
    
    return True


def verify_assistant_binary(assistant_file):
    """Verify the assistant binary structure."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("STEP 6: Verifying Assistant Binary")
    logger.info("=" * 70)
    
    assistant_file = Path(assistant_file)
    
    if not assistant_file.exists():
        logger.error(f"✗ Assistant file not found: {assistant_file}")
        return False
    
    # Read the file
    with open(assistant_file, "rb") as f:
        content = f.read()
    
    file_size = len(content)
    logger.info(f"Assistant file size: {file_size / 1024 / 1024:.2f} MB")
    
    # Check for shebang
    if content.startswith(b"#!/usr/bin/env python3"):
        logger.info("✓ Shebang present")
    else:
        logger.warning("✗ Shebang missing or incorrect")
    
    # Find payload marker
    import launcher
    marker = launcher.PAYLOAD_MARKER
    
    marker_pos = content.rfind(marker)
    if marker_pos == -1:
        logger.error("✗ Payload marker not found")
        return False
    
    logger.info(f"✓ Payload marker found at offset: {marker_pos}")
    
    # Check ZIP magic after marker
    zip_offset = marker_pos + len(marker)
    zip_magic = content[zip_offset:zip_offset+4]
    
    if zip_magic == b"PK\x03\x04":
        logger.info(f"✓ ZIP payload found at offset: {zip_offset}")
        logger.info(f"  ZIP magic: {zip_magic.hex()}")
    else:
        logger.error(f"✗ ZIP magic not found. Got: {zip_magic.hex()}")
        return False
    
    # Calculate sizes
    launcher_size = marker_pos
    payload_size = file_size - zip_offset
    
    logger.info("")
    logger.info("Binary Structure:")
    logger.info(f"  Launcher code: {launcher_size / 1024:.2f} KB")
    logger.info(f"  Payload size: {payload_size / 1024 / 1024:.2f} MB")
    logger.info(f"  Total size: {file_size / 1024 / 1024:.2f} MB")
    
    # Verify we can extract the ZIP
    logger.info("")
    logger.info("Testing ZIP extraction...")
    
    with tempfile.TemporaryDirectory() as temp_extract:
        temp_extract = Path(temp_extract)
        temp_zip = temp_extract / "test_payload.zip"
        
        # Extract payload to temp ZIP
        with open(assistant_file, "rb") as src:
            src.seek(zip_offset)
            with open(temp_zip, "wb") as dst:
                dst.write(src.read())
        
        # Try to open as ZIP
        try:
            with zipfile.ZipFile(temp_zip, "r") as zf:
                names = zf.namelist()
                logger.info(f"✓ ZIP is valid with {len(names)} files")
                
                # Check for required files
                has_rcc = any("rcc" in n for n in names)
                has_holotree = any(".rcc_home" in n for n in names)
                has_robot = any("robot/" in n for n in names)
                
                if has_rcc:
                    logger.info("  ✓ Contains RCC executable")
                if has_holotree:
                    holotree_files = [n for n in names if ".rcc_home" in n]
                    logger.info(f"  ✓ Contains Holotree ({len(holotree_files)} files)")
                if has_robot:
                    robot_files = [n for n in names if "robot/" in n]
                    logger.info(f"  ✓ Contains robot ({len(robot_files)} files)")
                
                return has_rcc and has_holotree and has_robot
                
        except zipfile.BadZipFile as e:
            logger.error(f"✗ ZIP validation failed: {e}")
            return False


def main():
    """Run the complete demonstration."""
    logger.info("=" * 70)
    logger.info("COMPLETE FETCH-REPOS-BOT INTEGRATION DEMONSTRATION")
    logger.info("=" * 70)
    logger.info("")
    
    # Create working directory
    with tempfile.TemporaryDirectory(prefix="rcc_demo_") as work_dir:
        work_dir = Path(work_dir)
        logger.info(f"Working directory: {work_dir}")
        logger.info("")
        
        # Step 1: Download RCC
        rcc_path = download_rcc(work_dir / "rcc_bin")
        if not rcc_path:
            logger.error("Failed to download RCC")
            return 1
        
        # Step 2: Clone fetch-repos-bot
        robot_dir = work_dir / "fetch-repos-bot"
        if not clone_fetch_repos_bot(robot_dir):
            logger.error("Failed to clone fetch-repos-bot")
            return 1
        
        # Step 3: Pre-build Holotree
        rcc_home_dir = work_dir / "rcc_home_build"
        if not prebuild_holotree(rcc_path, robot_dir, rcc_home_dir):
            logger.error("Failed to pre-build Holotree")
            return 1
        
        # Step 4: Create payload ZIP
        payload_zip = work_dir / "payload.zip"
        if not create_payload_with_embedded_holotree(
            rcc_path, rcc_home_dir, robot_dir, payload_zip
        ):
            logger.error("Failed to create payload")
            return 1
        
        # Step 5: Build self-extracting assistant
        assistant_file = work_dir / "assistant.py"
        if not build_self_extracting_assistant(payload_zip, assistant_file):
            logger.error("Failed to build assistant")
            return 1
        
        # Step 6: Verify binary
        if not verify_assistant_binary(assistant_file):
            logger.error("Binary verification failed")
            return 1
        
        # Success! Copy to current directory for inspection
        final_output = Path("demo_assistant.py")
        shutil.copy(assistant_file, final_output)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✓ DEMONSTRATION COMPLETE")
        logger.info("=" * 70)
        logger.info("")
        logger.info(f"Self-extracting assistant created: {final_output.resolve()}")
        logger.info(f"Size: {final_output.stat().st_size / 1024 / 1024:.2f} MB")
        logger.info("")
        logger.info("To test the assistant:")
        logger.info(f"  python {final_output}")
        logger.info("")
        logger.info("The assistant contains:")
        logger.info("  - Full launcher code")
        logger.info("  - RCC executable")
        logger.info("  - Pre-built Holotree environment")
        logger.info("  - fetch-repos-bot robot")
        logger.info("")
        
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        logger.error("\nInterrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
