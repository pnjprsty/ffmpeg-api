# Environment Configuration Guide

## Overview

Service FFmpeg API menggunakan `.env` file untuk konfigurasi yang mudah diubah tanpa perlu modifikasi code.

---

## Quick Start

### 1. Copy template `.env.example` ke `.env`
```bash
cp .env.example .env
```

### 2. Edit `.env` sesuai kebutuhan
```bash
# Edit OUTPUT_DIR ke path yang Anda inginkan
nano .env
```

### 3. Jalankan service
```bash
uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload
```

Service akan otomatis membaca konfigurasi dari `.env` file.

---

## Configuration Options

### OUTPUT_DIR
```
OUTPUT_DIR=/tmp/ffmpeg-output
```

**Deskripsi**: Directory untuk output files (videos, rendered content, dll)

**Options**:
- `/tmp/ffmpeg-output` - Development (writable untuk non-root)
- `/output` - Production (memerlukan setup dengan sudo)
- `/custom/path` - Custom directory (harus writable oleh service user)

**Default**: `/output` (jika tidak ada `.env`, akan fallback ke `/tmp/ffmpeg-output`)

---

### RENDER_TIMEOUT
```
RENDER_TIMEOUT=300
```

**Deskripsi**: Timeout untuk proses rendering dalam detik

**Options**: Integer value (e.g., 300 = 5 menit)

**Default**: `300`

---

### HOST
```
HOST=127.0.0.1
```

**Deskripsi**: Host/IP yang digunakan API server

**Options**:
- `127.0.0.1` - Localhost only (development)
- `0.0.0.0` - Listen on all interfaces (production)
- `192.168.1.100` - Specific IP

**Default**: `127.0.0.1`

---

### PORT
```
PORT=9000
```

**Deskripsi**: Port yang digunakan API server

**Options**: Integer 1-65535

**Default**: `9000`

---

### RELOAD
```
RELOAD=true
```

**Deskripsi**: Enable auto-reload on code changes (development only)

**Options**: `true` atau `false`

**Default**: `false`

---

### LOG_LEVEL
```
LOG_LEVEL=info
```

**Deskripsi**: Logging verbosity level

**Options**:
- `debug` - Verbose debugging info
- `info` - General information
- `warning` - Warnings only
- `error` - Errors only
- `critical` - Critical errors only

**Default**: `info`

---

### PUID / PGID
```
PUID=1000
PGID=1000
```

**Deskripsi**: Process User ID / Group ID untuk Docker container

**Options**: Integer UID/GID

**Default**: `1000`

---

## Examples

### Development Mode
```env
OUTPUT_DIR=/tmp/ffmpeg-output
HOST=127.0.0.1
PORT=9000
RELOAD=true
LOG_LEVEL=debug
RENDER_TIMEOUT=300
```

### Production Mode
```env
OUTPUT_DIR=/output
HOST=0.0.0.0
PORT=8000
RELOAD=false
LOG_LEVEL=info
RENDER_TIMEOUT=300
```

### Docker Mode
```env
OUTPUT_DIR=/output
HOST=0.0.0.0
PORT=8000
RELOAD=false
LOG_LEVEL=info
PUID=1000
PGID=1000
```

---

## Usage

### Method 1: Uvicorn with .env
```bash
# Service akan otomatis membaca .env
uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload
```

### Method 2: Override dengan environment variable
```bash
# Override OUTPUT_DIR dari command line
OUTPUT_DIR=/my/custom/path uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload
```

### Method 3: Docker Compose
```bash
# Docker Compose membaca .env otomatis
docker-compose up -d
```

### Method 4: Systemd Service
```bash
# Create .env di /opt/ffmpeg-api/
# Systemd akan load .env dari ExecStart directory
sudo systemctl start ffmpeg-api.service
```

---

## Verification

Check jika konfigurasi dimuat dengan benar:

```bash
# Python check
python3 -c "from app.config import settings; print(f'OUTPUT_DIR={settings.output_dir}')"

# Grep .env file
grep OUTPUT_DIR .env

# Check logs saat startup
# Look for: "Output directory ready: /tmp/ffmpeg-output"
```

---

## Common Issues

### Issue: Changes in .env tidak ter-apply
**Solution**: Restart service
```bash
# Hentikan service
CTRL+C

# Jalankan kembali
uvicorn app.main:app --host 127.0.0.1 --port 9000 --reload
```

### Issue: OUTPUT_DIR tidak writable
**Solution**: 
1. Check permissions
```bash
ls -la /tmp/ffmpeg-output
```

2. Fix permissions
```bash
chmod 755 /tmp/ffmpeg-output
chown $USER:$USER /tmp/ffmpeg-output
```

### Issue: .env file tidak ditemukan
**Solution**: 
1. Pastikan `.env` ada di root directory project
```bash
ls -la .env
```

2. Jika tidak ada, copy dari template
```bash
cp .env.example .env
```

---

## Security Notes

- `.env` file mungkin berisi sensitive information, **jangan commit ke git**
- Add `.env` ke `.gitignore` (sudah ditambahkan)
- Use `.env.example` sebagai template untuk documentation
- Change PUID/PGID sesuai kebutuhan security Anda

---

## Environment Variable Priority

1. **Highest**: Command line argument
   ```bash
   OUTPUT_DIR=/custom/path uvicorn ...
   ```

2. **Medium**: `.env` file
   ```env
   OUTPUT_DIR=/tmp/ffmpeg-output
   ```

3. **Lowest**: Hardcoded default
   ```python
   output_dir: str = Field(default="/output", ...)
   ```
