#!/usr/bin/env python3
"""
Test script for RCC Self-Extracting Assistant

This script performs basic validation of the launcher and builder
functionality without requiring actual RCC or robot files.
"""

import sys
import tempfile
import zipfile
from pathlib import Path
import shutil


def create_mock_payload(temp_dir):
    """Create a mock payload for testing."""
    print("Creating mock payload...")
    
    # Create mock RCC executable
    mock_rcc = temp_dir / "rcc.exe"
    mock_rcc.write_text("#!/usr/bin/env python3\nprint('Mock RCC')\n")
    mock_rcc.chmod(0o755)
    
    # Create mock .rcc_home
    mock_rcc_home = temp_dir / ".rcc_home"
    mock_rcc_home.mkdir()
    (mock_rcc_home / "test.txt").write_text("Mock Holotree")
    
    # Create mock robot
    mock_robot = temp_dir / "robot"
    mock_robot.mkdir()
    (mock_robot / "robot.yaml").write_text("tasks:\n  Run:\n    shell: echo 'Hello'\n")
    (mock_robot / "README.md").write_text("# Mock Robot")
    
    return mock_rcc, mock_rcc_home, mock_robot


def test_payload_marker_detection():
    """Test that launcher can detect the payload marker."""
    print("\n" + "=" * 60)
    print("TEST: Payload Marker Detection")
    print("=" * 60)
    
    # Import launcher module
    import launcher
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.py') as f:
        temp_file = Path(f.name)
        
        # Write some Python code
        f.write(b"# Test file\nprint('hello')\n")
        
        # Write marker
        f.write(b"\n# Payload marker\n")
        f.write(launcher.PAYLOAD_MARKER)
        
        # Write fake ZIP data
        f.write(b"PK\x03\x04FAKE_ZIP_DATA")
    
    try:
        offset = launcher.find_payload_offset(temp_file)
        
        if offset is not None:
            print(f"✓ Marker found at offset: {offset}")
            return True
        else:
            print("✗ Marker not found")
            return False
    finally:
        temp_file.unlink()


def test_builder_basic():
    """Test that builder can create a payload ZIP."""
    print("\n" + "=" * 60)
    print("TEST: Builder ZIP Creation")
    print("=" * 60)
    
    # Import builder module
    import builder
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock components
        mock_rcc, mock_rcc_home, mock_robot = create_mock_payload(temp_path)
        
        # Create output ZIP
        output_zip = temp_path / "payload.zip"
        
        # Create logger
        import logging
        logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        try:
            builder.create_payload_zip(
                mock_rcc,
                mock_rcc_home,
                mock_robot,
                output_zip,
                logger
            )
            
            # Verify ZIP was created
            if not output_zip.exists():
                print("✗ Payload ZIP not created")
                return False
            
            # Verify ZIP contents
            with zipfile.ZipFile(output_zip, 'r') as zf:
                names = zf.namelist()
                print(f"✓ Payload ZIP created with {len(names)} files")
                
                # Check for expected files
                expected = ['rcc.exe', '.rcc_home/test.txt', 'robot/robot.yaml']
                for exp in expected:
                    if exp in names:
                        print(f"  ✓ Found: {exp}")
                    else:
                        print(f"  ✗ Missing: {exp}")
                        return False
            
            return True
            
        except Exception as e:
            print(f"✗ Builder failed: {e}")
            return False


def test_extraction_path():
    """Test that extraction path is determined correctly."""
    print("\n" + "=" * 60)
    print("TEST: Extraction Path Detection")
    print("=" * 60)
    
    import launcher
    
    path = launcher.get_extraction_path()
    print(f"Extraction path: {path}")
    
    if sys.platform == "win32":
        if "AppData" in str(path) and "Local" in str(path):
            print("✓ Windows path looks correct")
            return True
        else:
            print("✗ Windows path doesn't look right")
            return False
    else:
        if ".local/share" in str(path):
            print("✓ Unix path looks correct")
            return True
        else:
            print("✗ Unix path doesn't look right")
            return False


def test_end_to_end_build():
    """Test end-to-end build process (without running)."""
    print("\n" + "=" * 60)
    print("TEST: End-to-End Build (Mock)")
    print("=" * 60)
    
    import builder
    import logging
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock components
        mock_rcc, mock_rcc_home, mock_robot = create_mock_payload(temp_path)
        
        # Create payload ZIP
        payload_zip = temp_path / "payload.zip"
        builder.create_payload_zip(
            mock_rcc,
            mock_rcc_home,
            mock_robot,
            payload_zip,
            logger
        )
        
        # Create self-extracting file
        launcher_path = Path(__file__).parent / "launcher.py"
        if not launcher_path.exists():
            print("✗ launcher.py not found, skipping")
            return False
        
        output_path = temp_path / "test_assistant.py"
        builder.create_self_extracting_file(
            launcher_path,
            payload_zip,
            output_path,
            logger
        )
        
        # Verify output
        if not output_path.exists():
            print("✗ Self-extracting file not created")
            return False
        
        size = output_path.stat().st_size
        print(f"✓ Self-extracting file created: {size:,} bytes")
        
        # Verify it contains the marker
        content = output_path.read_bytes()
        if b"===RCC_PAYLOAD_START===" in content:
            print("✓ Payload marker found in output")
            return True
        else:
            print("✗ Payload marker not found in output")
            return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("RCC Self-Extracting Assistant - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Payload Marker Detection", test_payload_marker_detection),
        ("Builder ZIP Creation", test_builder_basic),
        ("Extraction Path Detection", test_extraction_path),
        ("End-to-End Build", test_end_to_end_build),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
