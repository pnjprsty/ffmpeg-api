# FFmpeg API - Output Directory Fix Summary

## Problem Statement

Service FFmpeg API dapat mengalami error saat startup:
```
PermissionError: [Errno 13] Permission denied: '/output'
```

Ini terjadi ketika:
1. Direktori `/output` tidak ada atau tidak dapat ditulis
2. Permission ownership tidak cocok dengan user yang menjalankan service
3. Tidak ada mekanisme yang robust untuk setup permission saat startup

## Solution Overview

Solusi yang diimplementasikan memastikan direktori `/output` otomatis siap saat startup dengan permission yang tepat, tanpa menggunakan `chmod 777`.

## Files Modified/Created

### 1. **app/main.py** ✓
- **Perubahan**: Mengintegrasikan `OutputManager` di startup
- **Lokasi**: Import `setup_output_directory` dan `OutputDirectoryError` dari `output_manager`
- **Behavior**: Service gagal dengan error yang jelas jika `/output` tidak dapat ditulis
- **Lines**: 1-27 (initialization section)

```python
from .output_manager import setup_output_directory, OutputDirectoryError

try:
    setup_output_directory(OUTPUT_DIR)
    logger.info(f"Output directory ready: {OUTPUT_DIR}")
except OutputDirectoryError as e:
    logger.error(f"FATAL: Failed to setup output directory: {e}")
    raise SystemExit(f"Cannot start service: {e}")
```

### 2. **app/output_manager.py** (Sudah Ada, Dioptimalkan)
- **Fungsi**: `OutputManager` class melakukan:
  1. Membuat direktori jika belum ada
  2. Mengecek ownership user saat ini
  3. Memperbaiki permission jika perlu (755: rwxr-xr-x)
  4. Verifikasi directory writable
  5. Test write dengan temporary file
- **Lokasi Kunci**:
  - `ensure_directory_exists()`: Main method untuk setup
  - `_fix_permissions_if_needed()`: Fix permission jika user owns directory
  - `_test_write_access()`: Test write access dengan temp file

### 3. **Dockerfile** ✓
- **Perubahan**: 
  - Membuat non-root user `appuser` dengan UID 1000
  - Create `/output` dengan ownership `appuser:appuser`
  - Set permission 755 (rwxr-xr-x)
  - Run container sebagai non-root user
- **Lines**: 13-21, 35-38

```dockerfile
# Create non-root user
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g 1000 -s /sbin/nologin -c "Application user" appuser

# Create output directory with proper permissions
RUN mkdir -p /output && \
    chown 1000:1000 /output && \
    chmod 755 /output

USER appuser
```

### 4. **docker-compose.yml** ✓
- **Perubahan**:
  - Set `user: "1000:1000"` untuk match container UID/GID
  - Add `:rw` flag ke volume mount
  - Add dokumentasi tentang host directory setup
- **Lines**: 8, 13

```yaml
user: "1000:1000"
volumes:
  - ./output:/output:rw
```

### 5. **systemd/ffmpeg-api.service** (NEW)
- **File baru** untuk deployment sebagai systemd service
- **Konfigurasi**:
  - Run sebagai user `ffmpeg-api` (UID 1000)
  - `ReadWritePaths=/output` untuk permission yang aman
  - Security settings yang ketat (`ProtectSystem=strict`, dll)
  - Fail-fast dengan Restart dan StartLimitBurst
- **Setup**:
  ```bash
  sudo cp systemd/ffmpeg-api.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable ffmpeg-api.service
  ```

### 6. **SETUP_OUTPUT_DIRECTORY.md** (NEW)
- **Dokumentasi lengkap** dengan:
  - Docker Compose setup instructions
  - Systemd service setup instructions
  - Manual Python execution
  - Troubleshooting guide
  - Permission model explanation
  - Startup checks documentation

### 7. **scripts/setup-output-dir.sh** (NEW)
- **Helper script** untuk setup `/output` dengan permission yang benar
- **Usage**:
  ```bash
  bash scripts/setup-output-dir.sh /output 1000 1000
  ```
- **Verifies**: Directory creation, permission setting, write access test

### 8. **test_output_permissions.py** (NEW)
- **Test script** untuk verifikasi OutputManager functionality
- **Tests**:
  1. OutputManager initialization
  2. Directory creation
  3. Write access verification
  4. Permission check
  5. Temp file write/read/delete
  6. User/group info verification
  7. Failure case testing (expected failures)
- **Result**: ✓ ALL TESTS PASSED

## Permission Model

```
Directory: /output
Permissions: 755 (rwxr-xr-x)
  - Owner: read, write, execute
  - Group: read, execute
  - Others: read, execute

BUKAN chmod 777 (tidak aman)
BUKAN chmod 644 (tidak executable)
```

## Deployment Instructions

### Docker Compose
```bash
# Setup host directory
mkdir -p ./output
chmod 755 ./output
chown 1000:1000 ./output

# Run
docker-compose up -d

# Verify
docker-compose logs ffmpeg-api | grep "Output directory ready"
```

### Systemd Service
```bash
# Setup user dan directory
sudo useradd -r -s /bin/false -u 1000 ffmpeg-api
sudo mkdir -p /output
sudo chown ffmpeg-api:ffmpeg-api /output
sudo chmod 755 /output

# Install service
sudo cp systemd/ffmpeg-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable ffmpeg-api.service
sudo systemctl start ffmpeg-api.service

# Verify
sudo journalctl -u ffmpeg-api.service -f
```

### Manual Python
```bash
mkdir -p /output
chmod 755 /output
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Startup Behavior

### Success Case
```
INFO:app.output_manager:Ensuring output directory exists: /output
INFO:app.output_manager:Output directory created/exists: /output
INFO:app.output_manager:Output directory ready: /output
INFO:app.main:Starting FFmpeg Video Renderer API
```

### Failure Case
```
ERROR:app.output_manager:Cannot create output directory /output: [Errno 13] Permission denied
FATAL: Failed to setup output directory: Cannot create output directory /output...
SystemExit: Cannot start service: Cannot create output directory /output...
```

## Verification Checklist

- [x] Direktori `/output` otomatis dibuat saat startup
- [x] Permission 755 (tidak 777)
- [x] Ownership sesuai dengan user yang menjalankan service
- [x] Startup gagal dengan error yang jelas jika tidak dapat ditulis
- [x] Temporary file test untuk verifikasi write access
- [x] Docker Compose support dengan volume permissions
- [x] Systemd service configuration template
- [x] Setup script helper
- [x] Test script dengan semua test cases lulus
- [x] Dokumentasi lengkap

## Test Results

```
✓ PASS: Main functionality test
  - OutputManager initialized
  - Directory created with correct ownership
  - Directory writable
  - Permissions: 0o40755
  - Temp file write/read successful
  - User/group info correct

✓ PASS: Permission failure test (expected)
  - Correctly fails for restricted paths
  - Clear error message
```

## Security Notes

1. **No chmod 777**: Menggunakan minimal permissions (755)
2. **Non-root execution**: Service berjalan sebagai non-root user
3. **Proper ownership**: User/group yang menjalankan service
4. **Fail-fast**: Service gagal jika permission tidak OK
5. **Strict systemd settings**: `ProtectSystem=strict`, `ProtectHome=true`
6. **Write verification**: Test actual write access, bukan hanya stat

## Benefits

✅ Service bisa langsung dijalankan pada server baru tanpa manual permission setup  
✅ Clear error messages jika ada masalah permission  
✅ Support untuk Docker, Systemd, dan manual execution  
✅ Secure permission model tanpa `chmod 777`  
✅ Automated verification saat startup  
✅ Comprehensive documentation dan helper scripts
