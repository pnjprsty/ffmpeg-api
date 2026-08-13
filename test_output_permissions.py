#!/usr/bin/env python3

"""
Test script for verifying FFmpeg API output directory permissions.

This script tests the OutputManager implementation and verifies that
the /output directory can be created and written to properly.
"""

import os
import sys
import tempfile
import logging
from pathlib import Path

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.output_manager import OutputManager, OutputDirectoryError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_output_manager(output_path="/tmp/test_output"):
    """Test OutputManager with a test directory."""
    
    print("\n" + "="*60)
    print("FFmpeg API Output Directory Permission Test")
    print("="*60 + "\n")
    
    # Clean up test directory if it exists
    import shutil
    if Path(output_path).exists():
        shutil.rmtree(output_path)
    
    print(f"Test Directory: {output_path}")
    print()
    
    try:
        print("[TEST 1] Initialize OutputManager")
        manager = OutputManager(output_path)
        print("  ✓ OutputManager initialized")
        print()
        
        print("[TEST 2] Ensure directory exists and permissions are set")
        result_path = manager.ensure_directory_exists()
        print(f"  ✓ Directory created: {result_path}")
        print(f"  ✓ Directory exists: {result_path.exists()}")
        print()
        
        print("[TEST 3] Verify directory is writable")
        if os.access(output_path, os.W_OK):
            print("  ✓ Directory is writable")
        else:
            print("  ✗ Directory is NOT writable")
            return False
        print()
        
        print("[TEST 4] Check directory permissions")
        stat_info = os.stat(output_path)
        mode = stat_info.st_mode
        print(f"  Mode: {oct(mode)}")
        print(f"  Owner UID: {stat_info.st_uid}")
        print(f"  Owner GID: {stat_info.st_gid}")
        print(f"  Current UID: {os.getuid()}")
        print(f"  Current GID: {os.getgid()}")
        print()
        
        print("[TEST 5] Test write access with temp file")
        test_file = None
        try:
            # Create test file
            with tempfile.NamedTemporaryFile(
                mode='w',
                dir=output_path,
                prefix='test_',
                suffix='.txt',
                delete=False
            ) as f:
                test_file = f.name
                f.write("Permission test - this file will be deleted\n")
            
            # Verify we can read it back
            with open(test_file, 'r') as f:
                content = f.read()
                if "Permission test" in content:
                    print(f"  ✓ Created and read test file: {Path(test_file).name}")
                else:
                    print("  ✗ Test file content verification failed")
                    return False
            
            # Delete test file
            os.unlink(test_file)
            print("  ✓ Cleaned up test file")
            print()
            
        except (OSError, IOError) as e:
            print(f"  ✗ Write test failed: {e}")
            if test_file and os.path.exists(test_file):
                try:
                    os.unlink(test_file)
                except OSError:
                    pass
            return False
        
        print("[TEST 6] Verify user/group information")
        print(f"  Running as user: {manager.actual_user}")
        print(f"  Running as group: {manager.actual_group}")
        print()
        
        print("="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print()
        print("Summary:")
        print(f"  - Output directory: {output_path}")
        print(f"  - Directory writable: YES")
        print(f"  - Permissions: {oct(mode)}")
        print(f"  - Test file write: OK")
        print(f"  - Test file read: OK")
        print()
        
        return True
        
    except OutputDirectoryError as e:
        print(f"✗ TEST FAILED: {e}")
        print()
        return False
    
    finally:
        # Cleanup
        if Path(output_path).exists():
            import shutil
            shutil.rmtree(output_path)


def test_with_restricted_path():
    """Test with a restricted path (should fail gracefully)."""
    
    print("\n" + "="*60)
    print("Permission Failure Test (Expected to Fail)")
    print("="*60 + "\n")
    
    restricted_path = "/root/test_restricted"
    
    print(f"Test Directory: {restricted_path}")
    print("Expected: Should fail with permission error (non-root user)")
    print()
    
    try:
        manager = OutputManager(restricted_path)
        manager.ensure_directory_exists()
        print("✗ TEST UNEXPECTED: Should have failed but didn't")
        return False
    except OutputDirectoryError as e:
        print(f"✓ TEST PASSED: Got expected error")
        print(f"  Error message: {str(e)[:80]}...")
        print()
        return True
    except Exception as e:
        print(f"✗ TEST FAILED: Got unexpected error type: {type(e).__name__}")
        print(f"  Error: {e}")
        print()
        return False


def main():
    """Run all tests."""
    
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  FFmpeg API - Output Directory Permission Tests  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # Test 1: Main functionality test
    results.append(("Main functionality test", test_output_manager()))
    
    # Test 2: Failure case (if not root)
    if os.getuid() != 0:
        results.append(("Permission failure test (expected)", test_with_restricted_path()))
    else:
        print("\n[SKIPPED] Permission failure test (running as root)")
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*60 + "\n")
    
    # Exit code
    all_passed = all(result for _, result in results)
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
