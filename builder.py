#!/usr/bin/env python3
"""
Builder for Self-Extracting RCC Assistant

This script creates a self-contained assistant.py by combining:
1. launcher.py (the extraction and execution logic)
2. A payload marker
3. A ZIP file containing rcc.exe, .rcc_home, and the robot project

Usage:
    python builder.py --rcc path/to/rcc.exe \\
                      --rcc-home path/to/.rcc_home \\
                      --robot path/to/robot \\
                      --output assistant.py

The result is a single .py file that can be distributed and run without dependencies.
"""

import argparse
import logging
import shutil
import sys
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime


PAYLOAD_MARKER = b"===RCC_PAYLOAD_START==="


def setup_logging():
    """Configure logging to console."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)


def validate_inputs(rcc_path, robot_path, logger):
    """
    Validate that required input paths exist.
    
    Args:
        rcc_path: Path to RCC executable
        robot_path: Path to robot project directory
        logger: Logger instance
        
    Returns:
        True if all inputs are valid, False otherwise
    """
    valid = True
    
    if not rcc_path.exists():
        logger.error(f"RCC executable not found: {rcc_path}")
        valid = False
    elif not rcc_path.is_file():
        logger.error(f"RCC path is not a file: {rcc_path}")
        valid = False
    
    if not robot_path.exists():
        logger.error(f"Robot project not found: {robot_path}")
        valid = False
    elif not robot_path.is_dir():
        logger.error(f"Robot path is not a directory: {robot_path}")
        valid = False
    else:
        # Check for robot.yaml
        robot_yaml = robot_path / "robot.yaml"
        if not robot_yaml.exists():
            logger.warning(f"robot.yaml not found in {robot_path}")
            logger.warning("This may cause issues when running the assistant")
    
    return valid


def create_payload_zip(rcc_path, rcc_home_path, robot_path, output_zip, logger):
    """
    Create a ZIP file containing all required components.
    
    Args:
        rcc_path: Path to RCC executable
        rcc_home_path: Path to .rcc_home directory (optional)
        robot_path: Path to robot project directory
        output_zip: Path where ZIP file should be created
        logger: Logger instance
    """
    logger.info(f"Creating payload ZIP: {output_zip}")
    
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add RCC executable
        logger.info(f"Adding RCC: {rcc_path}")
        zf.write(rcc_path, rcc_path.name)
        
        # Add .rcc_home if provided
        if rcc_home_path and rcc_home_path.exists():
            logger.info(f"Adding RCC home: {rcc_home_path}")
            for file_path in rcc_home_path.rglob("*"):
                if file_path.is_file():
                    arcname = Path(".rcc_home") / file_path.relative_to(rcc_home_path)
                    zf.write(file_path, arcname)
                    if len(list(zf.namelist())) % 100 == 0:
                        logger.info(f"  Added {len(zf.namelist())} files...")
        
        # Add robot project
        logger.info(f"Adding robot project: {robot_path}")
        for file_path in robot_path.rglob("*"):
            if file_path.is_file():
                # Skip common ignore patterns
                if any(part.startswith(".") for part in file_path.parts):
                    continue
                if "__pycache__" in file_path.parts:
                    continue
                
                arcname = Path("robot") / file_path.relative_to(robot_path)
                zf.write(file_path, arcname)
        
        logger.info(f"Payload ZIP created with {len(zf.namelist())} files")
        
        # Calculate and log size
        zip_size = output_zip.stat().st_size
        logger.info(f"Payload size: {zip_size:,} bytes ({zip_size / 1024 / 1024:.2f} MB)")


def calculate_file_hash(file_path):
    """Calculate SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_self_extracting_file(launcher_path, payload_zip, output_path, logger):
    """
    Combine launcher.py and payload ZIP into a single self-extracting file.
    
    Args:
        launcher_path: Path to launcher.py
        payload_zip: Path to payload ZIP file
        output_path: Path where assistant.py should be created
        logger: Logger instance
    """
    logger.info(f"Creating self-extracting file: {output_path}")
    
    with open(output_path, "wb") as out:
        # Write launcher script
        logger.info("Writing launcher script...")
        with open(launcher_path, "rb") as launcher:
            out.write(launcher.read())
        
        # Write marker comment (for human readability)
        out.write(b"\n# " + b"=" * 70 + b"\n")
        out.write(b"# EMBEDDED PAYLOAD - DO NOT EDIT BELOW THIS LINE\n")
        out.write(b"# " + b"=" * 70 + b"\n")
        
        # Write payload marker
        out.write(PAYLOAD_MARKER)
        
        # Write payload ZIP
        logger.info("Writing payload ZIP...")
        with open(payload_zip, "rb") as payload:
            shutil.copyfileobj(payload, out)
    
    # Calculate final size and hash
    final_size = output_path.stat().st_size
    final_hash = calculate_file_hash(output_path)
    
    logger.info(f"Self-extracting file created successfully")
    logger.info(f"Final size: {final_size:,} bytes ({final_size / 1024 / 1024:.2f} MB)")
    logger.info(f"SHA256: {final_hash}")


def add_metadata(output_path, metadata, logger):
    """
    Add metadata as a comment at the beginning of the file.
    
    Args:
        output_path: Path to the assistant.py file
        metadata: Dictionary of metadata to include
        logger: Logger instance
    """
    logger.info("Adding metadata to output file...")
    
    # Read the current content
    with open(output_path, "rb") as f:
        content = f.read()
    
    # Create metadata header
    metadata_lines = [
        b"#!/usr/bin/env python3\n",
        b'"""\n',
        b"Self-Extracting RCC Assistant\n",
        b"\n",
        b"Build Information:\n",
    ]
    
    for key, value in metadata.items():
        metadata_lines.append(f"  {key}: {value}\n".encode())
    
    metadata_lines.append(b'"""\n\n')
    
    # Find where the actual launcher code starts (skip the original shebang and docstring)
    lines = content.split(b"\n")
    start_idx = 0
    in_docstring = False
    
    for i, line in enumerate(lines):
        if line.strip().startswith(b'"""'):
            if not in_docstring:
                in_docstring = True
            else:
                start_idx = i + 1
                break
        elif i == 0 and line.startswith(b"#!"):
            continue
    
    # Combine metadata and original content (skip original header)
    remaining_content = b"\n".join(lines[start_idx:])
    
    # Write back
    with open(output_path, "wb") as f:
        f.writelines(metadata_lines)
        f.write(remaining_content)


def main():
    """Main builder entry point."""
    parser = argparse.ArgumentParser(
        description="Build a self-extracting RCC assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python builder.py --rcc rcc.exe --robot my-robot --output assistant.py
  
  python builder.py --rcc rcc.exe \\
                    --rcc-home .rcc_home \\
                    --robot fetch-repos-bot \\
                    --output assistant.py
        """
    )
    
    parser.add_argument(
        "--rcc",
        type=Path,
        required=True,
        help="Path to RCC executable (rcc.exe or rcc)"
    )
    
    parser.add_argument(
        "--rcc-home",
        type=Path,
        help="Path to .rcc_home directory (optional, for offline mode)"
    )
    
    parser.add_argument(
        "--robot",
        type=Path,
        required=True,
        help="Path to robot project directory"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assistant.py"),
        help="Output path for self-extracting file (default: assistant.py)"
    )
    
    parser.add_argument(
        "--launcher",
        type=Path,
        default=Path(__file__).parent / "launcher.py",
        help="Path to launcher.py (default: launcher.py in same directory)"
    )
    
    parser.add_argument(
        "--temp-dir",
        type=Path,
        help="Temporary directory for build artifacts (default: system temp)"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("RCC Self-Extracting Assistant Builder")
    logger.info("=" * 60)
    
    # Validate inputs
    if not args.launcher.exists():
        logger.error(f"Launcher script not found: {args.launcher}")
        return 1
    
    if not validate_inputs(args.rcc, args.robot, logger):
        return 1
    
    # Setup temp directory
    if args.temp_dir:
        temp_dir = args.temp_dir
        temp_dir.mkdir(parents=True, exist_ok=True)
    else:
        import tempfile
        temp_dir = Path(tempfile.mkdtemp(prefix="rcc_builder_"))
    
    logger.info(f"Using temp directory: {temp_dir}")
    
    try:
        # Create payload ZIP
        payload_zip = temp_dir / "payload.zip"
        create_payload_zip(
            args.rcc,
            args.rcc_home,
            args.robot,
            payload_zip,
            logger
        )
        
        # Create self-extracting file
        create_self_extracting_file(
            args.launcher,
            payload_zip,
            args.output,
            logger
        )
        
        # Add metadata
        metadata = {
            "Build Date": datetime.now().isoformat(),
            "RCC Source": str(args.rcc.resolve()),
            "Robot Source": str(args.robot.resolve()),
            "RCC Home": str(args.rcc_home.resolve()) if args.rcc_home else "None",
        }
        add_metadata(args.output, metadata, logger)
        
        logger.info("=" * 60)
        logger.info("Build completed successfully!")
        logger.info(f"Output: {args.output.resolve()}")
        logger.info("=" * 60)
        logger.info("\nTo run the assistant:")
        logger.info(f"  python {args.output}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Build failed: {e}", exc_info=True)
        return 1
    
    finally:
        # Cleanup temp directory if we created it
        if not args.temp_dir and temp_dir.exists():
            logger.info(f"Cleaning up temp directory: {temp_dir}")
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
