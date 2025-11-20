#!/usr/bin/env python3
"""
Example Build Script for RCC Self-Extracting Assistant

This is a simple build automation script that wraps builder.py
with sensible defaults and validation.

Usage:
    python build.py
    python build.py --robot path/to/robot
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Build RCC self-extracting assistant with sensible defaults"
    )
    
    parser.add_argument(
        "--rcc",
        type=Path,
        default=Path("rcc.exe"),
        help="Path to RCC executable (default: rcc.exe)"
    )
    
    parser.add_argument(
        "--rcc-home",
        type=Path,
        help="Path to .rcc_home directory (default: auto-detect)"
    )
    
    parser.add_argument(
        "--robot",
        type=Path,
        default=Path("fetch-repos-bot"),
        help="Path to robot project (default: fetch-repos-bot)"
    )
    
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assistant.py"),
        help="Output file (default: assistant.py)"
    )
    
    parser.add_argument(
        "--download-robot",
        action="store_true",
        help="Download fetch-repos-bot if not present"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("RCC Self-Extracting Assistant - Build Script")
    print("=" * 60)
    
    # Validate files exist
    if not Path("builder.py").exists():
        print("ERROR: builder.py not found in current directory")
        return 1
    
    if not Path("launcher.py").exists():
        print("ERROR: launcher.py not found in current directory")
        return 1
    
    # Download robot if requested
    if args.download_robot and not args.robot.exists():
        print(f"\nDownloading {args.robot}...")
        result = subprocess.run([
            "git", "clone",
            "https://github.com/joshyorko/fetch-repos-bot.git",
            str(args.robot)
        ])
        if result.returncode != 0:
            print("ERROR: Failed to clone robot repository")
            return 1
    
    # Auto-detect RCC home if not specified
    if not args.rcc_home:
        # Try common locations
        candidates = [
            Path.home() / ".robocorp" / "holotree",
            Path.home() / ".rcc_home",
            Path(".rcc_home"),
        ]
        for candidate in candidates:
            if candidate.exists():
                args.rcc_home = candidate
                print(f"Auto-detected RCC home: {args.rcc_home}")
                break
    
    # Build command
    cmd = [
        sys.executable, "builder.py",
        "--rcc", str(args.rcc),
        "--robot", str(args.robot),
        "--output", str(args.output)
    ]
    
    if args.rcc_home:
        cmd.extend(["--rcc-home", str(args.rcc_home)])
    
    # Print configuration
    print("\nBuild Configuration:")
    print(f"  RCC:      {args.rcc}")
    print(f"  RCC Home: {args.rcc_home or 'Not specified'}")
    print(f"  Robot:    {args.robot}")
    print(f"  Output:   {args.output}")
    print()
    
    # Run builder
    print("Running builder...\n")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ Build completed successfully!")
        print("=" * 60)
        print(f"\nYour self-extracting assistant: {args.output}")
        print(f"\nTo run it:")
        print(f"  python {args.output}")
        return 0
    else:
        print("\n" + "=" * 60)
        print("✗ Build failed")
        print("=" * 60)
        return result.returncode


if __name__ == "__main__":
    sys.exit(main())
