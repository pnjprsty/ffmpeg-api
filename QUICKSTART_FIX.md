# Quick Fix for `/output` Permission Error

## Problem
Service gagal dengan error:
```
FATAL: Failed to setup output directory: Cannot create output directory /output: 
[Errno 13] Permission denied: '/output'
```

## Why This Happens
- `/output` adalah root-only directory di Linux
- Non-root user tidak dapat membuat directory di root path
- Ini adalah **EXPECTED BEHAVIOR** dan menunjukkan service bekerja dengan benar

## Solution 1: Docker Compose (Recommended)

```bash
# Step 1: Setup output directory di host
mkdir -p ./output
chmod 755 ./output
chown 1000:1000 ./output  # Match container UID

# Step 2: Jalankan service
docker-compose up -d

# Step 3: Verify
docker-compose logs ffmpeg-api | grep "Output directory ready"
```

## Solution 2: Custom Output Directory (Testing)

```bash
# Step 1: Buat directory yang writable
mkdir -p /tmp/ffmpeg-output
chmod 755 /tmp/ffmpeg-output

# Step 2: Jalankan dengan custom output dir
OUTPUT_DIR=/tmp/ffmpeg-output \
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Solution 3: Production Setup

```bash
# Step 1: Buat /output dengan proper permissions
sudo mkdir -p /output
sudo chown 1000:1000 /output    # atau ffmpeg-api:ffmpeg-api
sudo chmod 755 /output

# Step 2: Verify
ls -la /output

# Step 3: Jalankan service
# Service sekarang bisa write ke /output
```

## Verification

Jika setup berhasil, Anda akan melihat log:
```
INFO:app.output_manager:Output directory ready: /output
INFO:app.main:Starting FFmpeg Video Renderer API
```

## What Was Fixed

1. **Service sekarang fail-fast dengan clear error** jika `/output` tidak dapat ditulis
2. **Tidak menggunakan `chmod 777`** (secure permission 755)
3. **Proper user/group ownership** sesuai user yang menjalankan service
4. **Auto-directory creation** jika directory writable
5. **Write verification** dengan test file creation/deletion

## File Changes Made

- **app/main.py**: Integrasi OutputManager untuk startup checks
- **Dockerfile**: Non-root user dengan UID 1000 dan permission 755
- **docker-compose.yml**: User mapping dan volume permission
- **systemd/ffmpeg-api.service**: Production service template
- **test_output_permissions.py**: Comprehensive test scripts (✓ ALL TESTS PASSED)

Service siap untuk deployment pada server baru dengan proper setup!