#!/usr/bin/env python3
"""
Test to verify the PyInstaller UTF-8 fix.

This test demonstrates that:
1. Self-extracting files ARE created correctly with binary payloads
2. These files CANNOT be decoded as UTF-8 (which is expected and correct)
3. The launcher CAN read the payload correctly using binary mode
4. PyInstaller would fail on these files (which is why we build from launcher.py)
"""

import sys
import tempfile
import zipfile
from pathlib import Path
import shutil
import subprocess

# Add the repo to path
sys.path.insert(0, '/home/runner/work/rcc-selfextracting-assistant/rcc-selfextracting-assistant')

import builder
import launcher as launcher_module
import logging

def test_self_extracting_file_properties():
    """
    Test that demonstrates the UTF-8 issue and the fix.
    """
    print("="* 70)
    print("Testing Self-Extracting File Properties")
    print("="* 70)
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.WARNING)
    
    temp_dir = Path(tempfile.mkdtemp())
    print(f"\nWorking directory: {temp_dir}\n")
    
    try:
        # Create mock components
        print("1. Creating mock payload components...")
        mock_rcc = temp_dir / "rcc.exe"
        mock_rcc.write_text("#!/usr/bin/env python3\nimport sys\nprint('Mock RCC')\n")
        
        mock_rcc_home = temp_dir / ".rcc_home"
        mock_rcc_home.mkdir()
        (mock_rcc_home / "test.txt").write_text("Mock Holotree")
        
        mock_robot = temp_dir / "robot"
        mock_robot.mkdir()
        (mock_robot / "robot.yaml").write_text("tasks:\n  Run:\n    shell: echo 'Hello'\n")
        print("   ✓ Mock components created")
        
        # Create payload ZIP
        print("\n2. Creating payload ZIP...")
        payload_zip = temp_dir / "payload.zip"
        builder.create_payload_zip(mock_rcc, mock_rcc_home, mock_robot, payload_zip, logger)
        print(f"   ✓ Payload ZIP created: {payload_zip.stat().st_size} bytes")
        
        # Create self-extracting file
        print("\n3. Creating self-extracting file...")
        launcher_path = Path('/home/runner/work/rcc-selfextracting-assistant/rcc-selfextracting-assistant/launcher.py')
        output_path = temp_dir / "test_assistant.py"
        builder.create_self_extracting_file(launcher_path, payload_zip, output_path, logger)
        print(f"   ✓ Self-extracting file created: {output_path.stat().st_size:,} bytes")
        
        # Test 1: Verify file contains binary data that would cause UTF-8 errors
        print("\n4. Testing UTF-8 decoding (should FAIL - this is expected)...")
        with open(output_path, 'rb') as f:
            content = f.read()
        
        try:
            content.decode('utf-8')
            print("   ✗ ERROR: File is valid UTF-8 (unexpected!)")
            print("   This means the binary payload is missing or corrupt.")
            return False
        except UnicodeDecodeError as e:
            print(f"   ✓ UTF-8 decode failed as expected")
            print(f"   Error: {str(e)[:80]}...")
            print("   This is WHY PyInstaller fails on self-extracting files.")
        
        # Test 2: Verify the launcher can correctly find and read the payload
        print("\n5. Testing launcher's binary reading (should SUCCEED)...")
        offset = launcher_module.find_payload_offset(output_path)
        if offset is None:
            print("   ✗ ERROR: Launcher couldn't find payload marker")
            return False
        
        print(f"   ✓ Payload marker found at offset: {offset}")
        
        # Test 3: Verify the payload is a valid ZIP file
        print("\n6. Verifying payload is valid ZIP...")
        with open(output_path, 'rb') as f:
            f.seek(offset)
            first_bytes = f.read(4)
            
        if first_bytes[:2] == b'PK':
            print(f"   ✓ ZIP signature found: {first_bytes.hex()}")
        else:
            print(f"   ✗ ERROR: No ZIP signature at offset")
            print(f"   Expected: 504b (PK)")
            print(f"   Got: {first_bytes.hex()}")
            return False
        
        # Test 4: Try to simulate what PyInstaller does
        print("\n7. Simulating PyInstaller behavior...")
        print("   PyInstaller would call: importlib.util.decode_source(file_content)")
        print("   This requires the entire file to be valid UTF-8.")
        
        try:
            import importlib.util
            decoded = importlib.util.decode_source(content)
            print("   ✗ ERROR: decode_source() succeeded (unexpected!)")
            return False
        except (UnicodeDecodeError, SyntaxError) as e:
            print(f"   ✓ decode_source() failed as expected")
            print(f"   Error type: {type(e).__name__}")
            print(f"   This is the exact error that breaks PyInstaller.")
        
        print("\n" + "="* 70)
        print("SUMMARY")
        print("="* 70)
        print("\n✓ Self-extracting files work correctly:")
        print("  - File is created with embedded binary ZIP payload")
        print("  - Launcher can read payload using binary mode (rb)")
        print("  - Launcher finds marker using rfind() to get last occurrence")
        print("  - Launcher treats payload as raw bytes, not UTF-8\n")
        
        print("✗ PyInstaller cannot process these files:")
        print("  - File contains non-UTF-8 binary data")
        print("  - importlib.util.decode_source() fails")
        print("  - This is expected and cannot be fixed in launcher code\n")
        
        print("✓ Solution implemented:")
        print("  - GitHub Actions workflow now builds .exe from launcher.py")
        print("  - launcher.py is pure Python (no binary payload)")
        print("  - PyInstaller can successfully process launcher.py")
        print("  - Self-extracting .py files remain the recommended format\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    success = test_self_extracting_file_properties()
    
    print("="* 70)
    if success:
        print("✓ ALL TESTS PASSED")
        print("="* 70)
        sys.exit(0)
    else:
        print("✗ TESTS FAILED")
        print("="* 70)
        sys.exit(1)
