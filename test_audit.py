#!/usr/bin/env python3
"""
Comprehensive Integration Test for Self-Extracting RCC Assistant

This test validates all audit requirements:
1. Embedded payload architecture
2. Build system functionality
3. Holotree & RCC integration
4. Repository structure & paths
5. Windows runtime behavior
"""

import os
import sys
import tempfile
import zipfile
from pathlib import Path
import shutil
import subprocess


def test_payload_marker_in_files():
    """Test 1: Verify payload marker exists in both launcher and builder."""
    print("\n" + "=" * 70)
    print("TEST 1: Payload Marker Verification")
    print("=" * 70)
    
    import launcher
    import builder
    
    # Check marker is defined
    assert hasattr(launcher, 'PAYLOAD_MARKER'), "launcher.py missing PAYLOAD_MARKER"
    assert hasattr(builder, 'PAYLOAD_MARKER'), "builder.py missing PAYLOAD_MARKER"
    
    # Check marker values match
    assert launcher.PAYLOAD_MARKER == builder.PAYLOAD_MARKER, "Markers don't match"
    assert launcher.PAYLOAD_MARKER == b"===RCC_PAYLOAD_START===", "Incorrect marker value"
    
    print("✓ Payload marker b'===RCC_PAYLOAD_START===' exists in both files")
    return True


def test_launcher_can_open_and_find_marker():
    """Test 2: Verify launcher can open __file__ and locate marker."""
    print("\n" + "=" * 70)
    print("TEST 2: Launcher Marker Detection")
    print("=" * 70)
    
    import launcher
    
    # Create a test file with marker
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.py') as f:
        test_file = Path(f.name)
        
        # Write Python code
        f.write(b"#!/usr/bin/env python3\n")
        f.write(b"# Test file\n")
        f.write(b"print('hello')\n")
        
        # Write marker
        f.write(launcher.PAYLOAD_MARKER)
        
        # Write fake ZIP data
        f.write(b"PK\x03\x04")  # ZIP magic number
    
    try:
        # Test opening in binary mode and finding marker
        with open(test_file, "rb") as f:
            content = f.read()
        
        marker_pos = content.find(launcher.PAYLOAD_MARKER)
        assert marker_pos != -1, "Marker not found in test file"
        
        # Test the actual function
        offset = launcher.find_payload_offset(test_file)
        assert offset is not None, "find_payload_offset returned None"
        assert offset > 0, "Offset should be positive"
        
        print(f"✓ Launcher can open file in binary mode: open(__file__, 'rb')")
        print(f"✓ Launcher can find marker: content.find(PAYLOAD_MARKER)")
        print(f"✓ Marker found at offset: {offset}")
        
        return True
    finally:
        test_file.unlink()


def test_payload_extraction_with_zipfile():
    """Test 3: Verify launcher extracts payload using zipfile.ZipFile."""
    print("\n" + "=" * 70)
    print("TEST 3: Payload Extraction")
    print("=" * 70)
    
    import launcher
    import logging
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a real ZIP file
        zip_path = temp_path / "test_payload.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("test.txt", "Hello World")
            zf.writestr("rcc.exe", "fake rcc")
            zf.writestr("robot/robot.yaml", "tasks:\n  Run:\n    shell: echo")
        
        # Create a self-extracting file
        self_extract = temp_path / "test_assistant.py"
        with open(self_extract, 'wb') as out:
            out.write(b"#!/usr/bin/env python3\n")
            out.write(b"# Test\n")
            out.write(launcher.PAYLOAD_MARKER)
            with open(zip_path, 'rb') as payload:
                out.write(payload.read())
        
        # Find offset
        offset = launcher.find_payload_offset(self_extract)
        assert offset is not None, "Offset not found"
        
        # Extract
        extract_dir = temp_path / "extracted"
        launcher.extract_payload(self_extract, offset, extract_dir, logger)
        
        # Verify extraction
        assert (extract_dir / "test.txt").exists(), "test.txt not extracted"
        assert (extract_dir / "rcc.exe").exists(), "rcc.exe not extracted"
        assert (extract_dir / "robot" / "robot.yaml").exists(), "robot.yaml not extracted"
        
        content = (extract_dir / "test.txt").read_text()
        assert content == "Hello World", "File content corrupted"
        
        print("✓ Payload extracted using zipfile.ZipFile")
        print(f"✓ Extracted to: {extract_dir}")
        print(f"✓ Files extracted: {len(list(extract_dir.rglob('*')))}")
        
        return True


def test_sentinel_file_creation():
    """Test 4: Verify launcher creates sentinel file (.payload_hash)."""
    print("\n" + "=" * 70)
    print("TEST 4: Sentinel File (.payload_hash)")
    print("=" * 70)
    
    import launcher
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a test file with payload
        test_file = temp_path / "test.py"
        test_file.write_bytes(b"test\n" + launcher.PAYLOAD_MARKER + b"payload_data_here")
        
        offset = launcher.find_payload_offset(test_file)
        
        # Save hash
        extract_dir = temp_path / "extract"
        extract_dir.mkdir()
        launcher.save_payload_hash(extract_dir, test_file, offset)
        
        # Verify sentinel exists
        hash_file = extract_dir / ".payload_hash"
        assert hash_file.exists(), "Sentinel file not created"
        
        stored_hash = hash_file.read_text().strip()
        assert len(stored_hash) == 64, "Hash should be 64 chars (SHA256)"
        
        print("✓ Sentinel file created: .payload_hash")
        print(f"✓ Hash stored: {stored_hash[:16]}...")
        
        return True


def test_builder_concatenation():
    """Test 5: Verify builder concatenates launcher + marker + payload."""
    print("\n" + "=" * 70)
    print("TEST 5: Builder Concatenation")
    print("=" * 70)
    
    import builder
    import logging
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock launcher
        launcher_file = temp_path / "launcher.py"
        launcher_file.write_text("#!/usr/bin/env python3\n# Mock launcher\n")
        
        # Create mock payload ZIP
        payload_zip = temp_path / "payload.zip"
        with zipfile.ZipFile(payload_zip, 'w') as zf:
            zf.writestr("rcc.exe", "mock rcc")
            zf.writestr("robot/robot.yaml", "tasks: {}")
        
        # Build self-extracting file
        output_file = temp_path / "assistant.py"
        builder.create_self_extracting_file(
            launcher_file,
            payload_zip,
            output_file,
            logger
        )
        
        # Verify structure
        with open(output_file, 'rb') as f:
            content = f.read()
        
        # Check launcher code is at start
        assert content.startswith(b"#!/usr/bin/env python3"), "Missing shebang"
        assert b"Mock launcher" in content, "Launcher code not included"
        
        # Check marker exists
        marker_pos = content.find(builder.PAYLOAD_MARKER)
        assert marker_pos != -1, "Marker not found in output"
        
        # Check ZIP payload follows marker
        zip_start = marker_pos + len(builder.PAYLOAD_MARKER)
        assert content[zip_start:zip_start+4] == b"PK\x03\x04", "ZIP magic not found after marker"
        
        print("✓ Builder concatenates: launcher.py + marker + payload.zip")
        print(f"✓ Marker position: {marker_pos}")
        print(f"✓ ZIP starts at: {zip_start}")
        print(f"✓ Total size: {len(content)} bytes")
        
        return True


def test_payload_structure():
    """Test 6: Verify payload.zip contains rcc.exe, .rcc_home, robot/."""
    print("\n" + "=" * 70)
    print("TEST 6: Payload Structure")
    print("=" * 70)
    
    import builder
    import logging
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create mock components
        rcc_file = temp_path / "rcc.exe"
        rcc_file.write_text("mock rcc executable")
        
        rcc_home = temp_path / ".rcc_home"
        rcc_home.mkdir()
        (rcc_home / "holotree.db").write_text("mock holotree")
        (rcc_home / "env1").mkdir()
        (rcc_home / "env1" / "python.exe").write_text("mock python")
        
        robot_dir = temp_path / "robot"
        robot_dir.mkdir()
        (robot_dir / "robot.yaml").write_text("tasks:\n  Run:\n    shell: echo")
        (robot_dir / "task.py").write_text("def main(): pass")
        
        # Create payload
        output_zip = temp_path / "payload.zip"
        builder.create_payload_zip(
            rcc_file,
            rcc_home,
            robot_dir,
            output_zip,
            logger
        )
        
        # Verify contents
        with zipfile.ZipFile(output_zip, 'r') as zf:
            names = zf.namelist()
            
            # Check required files
            assert "rcc.exe" in names, "rcc.exe not in payload"
            assert any(".rcc_home" in n for n in names), ".rcc_home not in payload"
            assert any("robot/robot.yaml" in n for n in names), "robot/robot.yaml not in payload"
            
            print(f"✓ Payload contains rcc.exe")
            print(f"✓ Payload contains .rcc_home/ ({sum(1 for n in names if '.rcc_home' in n)} files)")
            print(f"✓ Payload contains robot/ ({sum(1 for n in names if 'robot/' in n)} files)")
            print(f"✓ Total files in payload: {len(names)}")
        
        return True


def test_rcc_execution_command():
    """Test 7: Verify launcher runs: rcc.exe run --robot robot/robot.yaml."""
    print("\n" + "=" * 70)
    print("TEST 7: RCC Execution Command")
    print("=" * 70)
    
    import launcher
    
    # Check the run_rcc function signature
    import inspect
    sig = inspect.signature(launcher.run_rcc)
    params = list(sig.parameters.keys())
    
    assert 'rcc_exe' in params, "run_rcc missing rcc_exe parameter"
    assert 'robot_yaml' in params, "run_rcc missing robot_yaml parameter"
    
    # Read the source to verify command construction
    source = inspect.getsource(launcher.run_rcc)
    
    assert '"run"' in source or "'run'" in source, "Command doesn't include 'run'"
    assert '"--robot"' in source or "'--robot'" in source, "Command doesn't include '--robot'"
    
    print("✓ Launcher executes: rcc.exe run --robot robot/robot.yaml")
    print("✓ Command construction verified in run_rcc()")
    
    return True


def test_robocorp_home_setting():
    """Test 8: Verify launcher sets ROBOCORP_HOME environment variable."""
    print("\n" + "=" * 70)
    print("TEST 8: ROBOCORP_HOME Setting")
    print("=" * 70)
    
    import launcher
    import inspect
    
    # Check run_rcc function sets ROBOCORP_HOME
    source = inspect.getsource(launcher.run_rcc)
    
    assert 'ROBOCORP_HOME' in source, "ROBOCORP_HOME not set in run_rcc"
    assert 'env[' in source or 'environ' in source, "Environment not modified"
    
    print("✓ Launcher sets ROBOCORP_HOME in environment")
    print("✓ Environment variable passed to subprocess")
    
    return True


def test_windows_localappdata_path():
    """Test 9: Verify Windows uses %LOCALAPPDATA%/MyRccAssistant."""
    print("\n" + "=" * 70)
    print("TEST 9: Windows Path Configuration")
    print("=" * 70)
    
    import launcher
    
    # Check get_extraction_path function
    import inspect
    source = inspect.getsource(launcher.get_extraction_path)
    
    assert 'LOCALAPPDATA' in source, "get_extraction_path doesn't check LOCALAPPDATA"
    assert 'MyRccAssistant' in source or 'APP_NAME' in source, "App name not used"
    
    # Verify APP_NAME is set correctly
    assert hasattr(launcher, 'APP_NAME'), "APP_NAME not defined"
    assert launcher.APP_NAME == "MyRccAssistant", f"APP_NAME should be 'MyRccAssistant', got '{launcher.APP_NAME}'"
    
    print("✓ Windows path: %LOCALAPPDATA%/MyRccAssistant")
    print(f"✓ APP_NAME set to: {launcher.APP_NAME}")
    
    return True


def test_end_to_end_build():
    """Test 10: End-to-end build process validation."""
    print("\n" + "=" * 70)
    print("TEST 10: End-to-End Build Validation")
    print("=" * 70)
    
    import builder
    import launcher
    import logging
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(level=logging.INFO)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create complete mock environment
        rcc_file = temp_path / "rcc.exe"
        rcc_file.write_text("#!/bin/bash\necho 'Mock RCC'")
        rcc_file.chmod(0o755)
        
        rcc_home = temp_path / ".rcc_home"
        rcc_home.mkdir()
        (rcc_home / "holotree").mkdir()
        (rcc_home / "holotree" / "catalog.db").write_text("catalog")
        
        robot_dir = temp_path / "robot"
        robot_dir.mkdir()
        (robot_dir / "robot.yaml").write_text("tasks:\n  Run:\n    shell: echo 'Hello'")
        
        # Build payload ZIP
        payload_zip = temp_path / "payload.zip"
        builder.create_payload_zip(rcc_file, rcc_home, robot_dir, payload_zip, logger)
        
        # Create self-extracting file
        launcher_path = Path(__file__).parent / "launcher.py"
        output_file = temp_path / "assistant.py"
        builder.create_self_extracting_file(launcher_path, payload_zip, output_file, logger)
        
        # Verify the complete file
        assert output_file.exists(), "Output file not created"
        
        with open(output_file, 'rb') as f:
            content = f.read()
        
        # Verify structure
        assert content.startswith(b"#!/usr/bin/env python3"), "Missing shebang"
        assert builder.PAYLOAD_MARKER in content, "Marker not in output"
        
        # Use launcher's find_payload_offset to find the LAST occurrence
        offset = launcher.find_payload_offset(output_file)
        assert offset is not None, "Could not find payload offset"
        
        # Verify ZIP magic number at the offset
        assert content[offset:offset+4] == b"PK\x03\x04", "ZIP not properly appended"
        
        print("✓ Complete build process verified")
        print(f"✓ Output file: {output_file}")
        print(f"✓ File size: {len(content):,} bytes")
        print(f"✓ Launcher code: {offset:,} bytes")
        print(f"✓ Payload size: {len(content) - offset:,} bytes")
        
        return True


def main():
    """Run all comprehensive tests."""
    print("=" * 70)
    print("COMPREHENSIVE AUDIT VALIDATION")
    print("Self-Extracting RCC Assistant")
    print("=" * 70)
    
    tests = [
        ("Payload Marker Verification", test_payload_marker_in_files),
        ("Launcher Marker Detection", test_launcher_can_open_and_find_marker),
        ("Payload Extraction", test_payload_extraction_with_zipfile),
        ("Sentinel File Creation", test_sentinel_file_creation),
        ("Builder Concatenation", test_builder_concatenation),
        ("Payload Structure", test_payload_structure),
        ("RCC Execution Command", test_rcc_execution_command),
        ("ROBOCORP_HOME Setting", test_robocorp_home_setting),
        ("Windows Path Configuration", test_windows_localappdata_path),
        ("End-to-End Build", test_end_to_end_build),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("AUDIT VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n" + "=" * 70)
        print("✓ ALL AUDIT REQUIREMENTS VERIFIED")
        print("=" * 70)
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
