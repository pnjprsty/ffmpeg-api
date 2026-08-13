#!/usr/bin/env python3
"""Quick test script for the FFmpeg Video Renderer API"""

import subprocess
import time
import sys
import os

def check_ffmpeg():
    """Check if FFmpeg and ffprobe are available"""
    print("Checking FFmpeg installation...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        subprocess.run(["ffprobe", "-version"], capture_output=True, check=True)
        print("✓ FFmpeg and ffprobe are available")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"✗ FFmpeg/ffprobe not available: {e}")
        return False

def check_python_imports():
    """Check if Python modules can be imported"""
    print("\nChecking Python imports...")
    modules = ["fastapi", "uvicorn", "pydantic"]
    
    for module in modules:
        try:
            __import__(module)
            print(f"✓ {module} is importable")
        except ImportError as e:
            print(f"✗ {module} not importable: {e}")
            return False
    
    # Try importing our app
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.main import app
        from app.models import Scene, RenderRequest
        from app.ffmpeg import check_ffmpeg_installed
        print("✓ All application modules can be imported")
        return True
    except ImportError as e:
        print(f"✗ Application modules import failed: {e}")
        return False

def check_directory_structure():
    """Check if all required directories exist"""
    print("\nChecking directory structure...")
    required_dirs = [
        "app",
        "output"
    ]
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    all_good = True
    
    for dir_name in required_dirs:
        dir_path = os.path.join(current_dir, dir_name)
        if os.path.isdir(dir_path):
            print(f"✓ Directory exists: {dir_name}")
        else:
            print(f"✗ Missing directory: {dir_name}")
            all_good = False
    
    return all_good

def check_docker_files():
    """Check if Docker configuration files exist"""
    print("\nChecking Docker configuration...")
    required_files = [
        "Dockerfile",
        "docker-compose.yml",
        ".dockerignore",
        "requirements.txt"
    ]
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    all_good = True
    
    for file_name in required_files:
        file_path = os.path.join(current_dir, file_name)
        if os.path.isfile(file_path):
            print(f"✓ File exists: {file_name}")
        else:
            print(f"✗ Missing file: {file_name}")
            all_good = False
    
    return all_good

def main():
    """Run all checks"""
    print("=" * 60)
    print("FFmpeg Video Renderer API - System Test")
    print("=" * 60)
    
    # Run all checks
    tests = [
        ("FFmpeg Check", check_ffmpeg),
        ("Python Imports", check_python_imports),
        ("Directory Structure", check_directory_structure),
        ("Docker Configuration", check_docker_files),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{test_name}:")
            print("-" * 40)
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! The API is ready to use.")
        print("\nQuick Start Commands:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run API: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("3. Test API: curl http://localhost:8000/health")
        print("4. Use Docker: docker-compose up -d")
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
