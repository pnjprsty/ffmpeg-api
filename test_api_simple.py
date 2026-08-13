#!/usr/bin/env python3
"""Simple test script for the FFmpeg Video Renderer API"""

import subprocess
import os
import sys

def check_system():
    """Check system dependencies"""
    print("Checking system dependencies...")
    
    # Check FFmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✓ FFmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ FFmpeg is NOT available")
        return False
    
    # Check ffprobe
    try:
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        print("✓ ffprobe is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ ffprobe is NOT available")
        return False
    
    return True

def check_python_modules():
    """Check Python modules"""
    print("\nChecking Python modules...")
    
    modules_to_check = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("pydantic", "Pydantic"),
    ]
    
    all_good = True
    for module_name, display_name in modules_to_check:
        try:
            __import__(module_name)
            print(f"✓ {display_name} module available")
        except ImportError:
            print(f"✗ {display_name} module NOT available")
            all_good = False
    
    return all_good

def check_directory_structure():
    """Check project structure"""
    print("\nChecking project structure...")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "app/__init__.py",
        "app/main.py", 
        "app/models.py",
        "app/ffmpeg.py",
        "app/renderer.py",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
    ]
    
    all_good = True
    for file_path in required_files:
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} NOT found")
            all_good = False
    
    return all_good

def check_code_compilation():
    """Check if code compiles"""
    print("\nChecking code compilation...")
    
    try:
        result = subprocess.run(
            ["python3", "-m", "compileall", "app"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✓ All Python files compile successfully")
            return True
        else:
            print("✗ Some Python files failed to compile")
            print(f"Error: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print("✗ Compilation timeout")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("FFmpeg Video Renderer API - Simple System Test")
    print("=" * 60)
    
    tests = [
        ("System Dependencies", check_system),
        ("Python Modules", check_python_modules),
        ("Project Structure", check_directory_structure),
        ("Code Compilation", check_code_compilation),
    ]
    
    results = []
    all_passed = True
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
            if not result:
                all_passed = False
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
            all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nThe FFmpeg Video Renderer API is ready to use.")
        print("\nQuick commands to start:")
        print("  Local: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("  Docker: docker-compose up -d")
        print("\nDocumentation: README.md and QUICKSTART.md")
    else:
        print("❌ Some tests failed. Please check above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
