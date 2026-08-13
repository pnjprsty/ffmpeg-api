# FFmpeg API - Output Directory Setup Guide

## Overview

Service ini memastikan direktori `/output` otomatis dibuat dan dikonfigurasi dengan permission yang tepat saat startup. Tidak ada perlu menggunakan `chmod 777`.

## Deployment Methods

### 1. Docker Compose (Recommended for Development/Testing)

#### Setup:
```bash
# Buat direktori output dengan permission yang tepat
mkdir -p ./output
chmod 755 ./output
chown 1000:1000 ./output

# Jalankan service
docker-compose up -d
```

#### Verifikasi:
```bash
# Check container logs untuk permission verification
docker-compose logs -f ffmpeg-api | grep "Output directory"

# Test API
curl http://localhost:8000/health

# Test write access dengan membuat file test
docker exec ffmpeg-video-renderer test -w /output && echo "Write permission OK"
```

#### Troubleshooting:
Jika mendapat error `Permission denied: '/output'`:
```bash
# Pastikan host directory ownership
ls -la ./output
# Output harus: drwxr-xr-x user:group

# Fix jika diperlukan
sudo chown 1000:1000 ./output
sudo chmod 755 ./output

# Rebuild dan restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

### 2. Systemd Service (Production)

#### Prerequisite:
```bash
# Buat user khusus untuk service
sudo useradd -r -s /bin/false -u 1000 ffmpeg-api

# Buat direktori output dengan ownership yang tepat
sudo mkdir -p /output
sudo chown ffmpeg-api:ffmpeg-api /output
sudo chmod 755 /output
```

#### Installation:
```bash
# Copy service file
sudo cp systemd/ffmpeg-api.service /etc/systemd/system/

# Update path di service file sesuai instalasi Anda
# Edit: /etc/systemd/system/ffmpeg-api.service
# Ubah WorkingDirectory dan ExecStart sesuai direktori instalasi

# Reload systemd
sudo systemctl daemon-reload

# Enable dan start service
sudo systemctl enable ffmpeg-api.service
sudo systemctl start ffmpeg-api.service
```

#### Verifikasi:
```bash
# Check status
sudo systemctl status ffmpeg-api.service

# View logs
sudo journalctl -u ffmpeg-api.service -f

# Test API
curl http://localhost:8000/health

# Verify /output permissions
ls -la /output
stat /output
```

#### Troubleshooting:
```bash
# Jika startup gagal, check log detail
sudo journalctl -u ffmpeg-api.service -n 50 --no-pager

# Verify user dan permission
sudo -u ffmpeg-api test -w /output && echo "OK" || echo "FAIL"

# Fix permission jika perlu
sudo chown -R ffmpeg-api:ffmpeg-api /output
sudo chmod 755 /output
```

---

### 3. Manual Python Execution

#### Setup:
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Buat output directory
mkdir -p /output
# Jika running as non-root, pastikan permission OK
chmod 755 /output
```

#### Run:
```bash
# Dengan default /output
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Atau dengan custom OUTPUT_DIR
OUTPUT_DIR=/custom/path python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Verifikasi:
```bash
# Jika melihat log:
# "Output directory ready: /output"
# Service siap dan /output dapat ditulis

# Test API
curl http://localhost:8000/health
```

---

## Environment Variables

```bash
# OUTPUT_DIR: Path ke direktori output (default: /output)
OUTPUT_DIR=/output

# RENDER_TIMEOUT: Timeout untuk rendering dalam detik (default: 300)
RENDER_TIMEOUT=300
```

---

## Permission Model

Service menggunakan model permission yang aman:

| Scenario | Permission | Owner | Group | Note |
|----------|-----------|-------|-------|------|
| Docker Container | 755 | 1000 | 1000 | Non-root user di container |
| Systemd Service | 755 | ffmpeg-api | ffmpeg-api | Dedicated user untuk service |
| Manual Execution | 755 | $USER | $USER | User yang menjalankan script |

**Model 755 (rwxr-xr-x):**
- Owner: read, write, execute
- Group: read, execute
- Others: read, execute

---

## Startup Checks

Service melakukan check berikut saat startup:

1. **Directory Creation**: Membuat `/output` jika belum ada
2. **Ownership Check**: Memastikan current user dapat write ke direktori
3. **Permission Verification**: Mengecek r/w/x permissions
4. **Write Test**: Membuat temporary file untuk test write access
5. **Cleanup**: Menghapus temporary file setelah test

Jika salah satu check gagal, service **GAGAL** dengan error yang jelas.

---

## Logs Output

Pada startup yang sukses, Anda akan melihat:

```
INFO:app.main:Ensuring output directory exists: /output
INFO:app.main:Output directory created/exists: /output
INFO:app.main:Output directory ready: /output
INFO:app.main:Starting FFmpeg Video Renderer API
```

Pada startup yang gagal:

```
ERROR:app.output_manager:FATAL: Failed to setup output directory: 
  Cannot write test file to output directory: Permission denied
FATAL: Failed to setup output directory: 
  Cannot write test file to output directory: Permission denied
```

---

## Security Notes

1. **Tidak menggunakan chmod 777**: Service menggunakan minimal permissions (755)
2. **Non-root execution**: Baik di Docker maupun Systemd, service berjalan sebagai non-root user
3. **Permission ownership**: Menggunakan user/group yang menjalankan service
4. **Strict systemd security**: Menggunakan `ProtectSystem=strict`, `ProtectHome=true`, dll
5. **Fail-fast**: Service gagal dengan error yang jelas jika permission tidak OK

---

## Common Issues & Solutions

### Issue: `Permission denied: '/output'`

**Cause**: Output directory tidak dapat ditulis oleh service user

**Solution**:
```bash
# Cek ownership
ls -la /output

# Fix ownership sesuai service user
sudo chown SERVICE_USER:SERVICE_USER /output
sudo chmod 755 /output
```

### Issue: `Cannot write test file to output directory`

**Cause**: Permission check gagal pada startup

**Solution**:
```bash
# Verify permission
stat /output

# Ensure write permission
chmod u+w /output
```

### Issue: Docker: `Permission denied on volume mount`

**Cause**: Host directory ownership tidak match dengan container user (1000:1000)

**Solution**:
```bash
# Check host directory
ls -la ./output

# Fix ownership
chown 1000:1000 ./output
chmod 755 ./output
```

---

## Testing

```bash
# Test dengan API call
curl -X POST http://localhost:8000/render \
  -H "Content-Type: application/json" \
  -d @request.json

# Verify output file dibuat
ls -la /output/
```

---

## Support Files

- `app/output_manager.py`: Main permission management logic
- `app/main.py`: Integration di startup
- `Dockerfile`: Container configuration
- `docker-compose.yml`: Docker compose setup
- `systemd/ffmpeg-api.service`: Systemd service configuration
