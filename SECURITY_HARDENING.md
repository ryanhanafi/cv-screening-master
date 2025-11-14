# Security Hardening Guide

Dokumen ini mencakup langkah-langkah hardening keamanan yang telah diterapkan dan rekomendasi lanjutan untuk deployment production.

## Status Implementasi

### ✅ Selesai

1. **Rate Limiting (Aplikasi Level)**
   - Django REST Framework throttle classes sudah diterapkan
   - Endpoint `/api/upload/` dibatasi 5 requests/minute per IP/user
   - Endpoint `/api/evaluate/` dibatasi 2 requests/minute per IP/user
   - File: `core/throttles.py`, `api/views.py`, `cv_screening/settings.py`

2. **Upload File Validation**
   - Batasan ukuran: 2 MB per file (`FILE_UPLOAD_MAX_MEMORY_SIZE`)
   - Tipe file diizinkan: PDF, DOC, DOCX
   - Implementasi di: `api/serializers.py`

3. **TLS & Security Headers**
   - `SECURE_SSL_REDIRECT = True` (enforce HTTPS)
   - `SECURE_HSTS_SECONDS = 31536000` (1 tahun)
   - `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`
   - `X_FRAME_OPTIONS = 'DENY'` (clickjacking protection)
   - `SECURE_CONTENT_TYPE_NOSNIFF = True`
   - `SECURE_BROWSER_XSS_FILTER = True`
   - Implementasi di: `cv_screening/settings.py`

4. **Celery Task Protection**
   - Rate limit task: `5/minute`
   - Time limit per task: 300 detik (5 menit)
   - Implementasi di: `evaluations/tasks.py`

5. **Input Validation**
   - Semua field di serializer memiliki constraints (max_length, required)
   - File content-type & size validation
   - Implementasi di: `api/serializers.py`

### 🔄 Sedang Dikerjakan / Rekomendasi

6. **Rate Limiting Edge/Proxy (Nginx)**
7. **Login Brute-Force Protection (django-axes)**

---

## Implementasi Tahap Lanjut

### A. Nginx Rate Limiting (DDoS Protection Awal)

Terapkan pada config nginx server Anda di `nginx.conf`:

```nginx
http {
    # Define rate limit zones
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=20r/s;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    
    # Connection limits (prevent slowloris attacks)
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    upstream django_backend {
        server 127.0.0.1:8000;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /path/to/cert.crt;
        ssl_certificate_key /path/to/key.key;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

        # Rate limiting for upload
        location /api/upload/ {
            limit_req zone=upload_limit burst=5 nodelay;
            limit_conn conn_limit 10;
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Rate limiting for general API
        location /api/ {
            limit_req zone=api_limit burst=10 nodelay;
            limit_conn conn_limit 20;
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Rate limiting for login
        location /admin/login/ {
            limit_req zone=login_limit burst=2 nodelay;
            proxy_pass http://django_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files (no rate limit needed)
        location /static/ {
            alias /path/to/project/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }
}
```

**Penjelasan:**
- `limit_req_zone`: mendefinisikan zona pembatasan (10m = 10MB memory)
- `limit_conn_zone`: membatasi jumlah koneksi simultane per IP
- `burst=5`: memungkinkan burst singkat (mitigasi spikes normal)
- `nodelay`: proses burst langsung (tidak tunda)
- `proxy_set_header X-Real-IP`: teruskan IP asli ke Django

**Konfigurasi di Django:**
Pastikan `SECURE_PROXY_SSL_HEADER` di settings jika di belakang proxy:
```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

---

### B. Proteksi Login Brute-Force (django-axes)

Lindungi endpoint login dari brute-force attacks.

**1. Install:**
```bash
pip install django-axes
```

**2. Update `requirements.txt`:**
```
django-axes
```

**3. Update `cv_screening/settings.py`:**
```python
INSTALLED_APPS = [
    # ... existing apps
    'axes',
]

MIDDLEWARE = [
    # ... existing middleware
    'axes.middleware.AxesMiddleware',  # letakkan di akhir
]

# django-axes configuration
AXES_FAILURE_LIMIT = 5  # lockout setelah 5 gagal
AXES_COOLOFF_DURATION = 1  # hour
AXES_LOCK_OUT_AT_FAILURE = True
AXES_USE_USER_AGENT = True
AXES_LOCKOUT_TEMPLATE = 'axes/lockout.html'  # optional custom template

# Jika ingin email notification
AXES_VERBOSE = True
```

**4. Run migrasi:**
```bash
python manage.py migrate
```

**5. (Optional) Custom lockout template:**
Buat `templates/axes/lockout.html`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Account Locked</title>
</head>
<body>
    <h1>Account Temporarily Locked</h1>
    <p>Terlalu banyak percobaan login gagal. Silakan coba lagi dalam {{ lockout_time }} menit.</p>
</body>
</html>
```

**6. Admin site protection:**
```python
# di cv_screening/urls.py
from axes.decorators import axes_dispatch_decorator

# Jika menggunakan default admin
admin.site.admin_view = axes_dispatch_decorator(admin.site.admin_view)
```

---

### C. Secrets Management (Environment Variables)

Hindari hardcode secrets di settings.

**1. Install:**
```bash
pip install django-environ
```

**2. Buat file `.env` di root project:**
```
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DATABASE_URL=sqlite:///db.sqlite3
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SECURE_SSL_REDIRECT=True
```

**3. Update `cv_screening/settings.py`:**
```python
import environ
import os

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost'])
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

# Celery
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
```

**4. Update `.gitignore`:**
```
.env
.env.local
*.pyc
__pycache__/
*.sqlite3
media/
/static/
```

**5. Update `requirements.txt`:**
```
django-environ
```

---

### D. Logging & Monitoring

**1. Request logging:**
Tambahkan di `cv_screening/settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'axes': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
        },
    },
}
```

Buat folder logs:
```bash
mkdir logs
```

**2. Sentry Integration (Error Tracking):**
```bash
pip install sentry-sdk
```

Di `cv_screening/settings.py`:
```python
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://your-sentry-dsn@sentry.io/project-id",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,  # 10% sample rate
    send_default_pii=False,
)
```

---

## Testing

### Run Unit Tests
```bash
python manage.py test api.tests
```

Tests mencakup:
- Upload throttling (5/minute)
- Evaluate throttling (2/minute)
- File validation (size & content-type)
- Unauthenticated access denial

### Load Testing dengan Locust

**1. Install:**
```bash
pip install locust
```

**2. Buat `locustfile.py` di root:**
```python
from locust import HttpUser, task, between
import json
import uuid

class CVScreeningUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Login (jika diperlukan)
        pass

    @task(3)
    def upload_file(self):
        file_data = {
            'file': ('test.pdf', b'%PDF-1.4\ntest', 'application/pdf')
        }
        self.client.post('/api/upload/', files=file_data)

    @task(1)
    def evaluate(self):
        payload = {
            'job_title': 'Test Job',
            'cv_id': str(uuid.uuid4()),
            'project_report_id': str(uuid.uuid4())
        }
        self.client.post('/api/evaluate/', json=payload)
```

**3. Jalankan:**
```bash
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10
```

---

## Deployment Checklist

- [ ] Set `DEBUG=False` di production
- [ ] Gunakan environment variables untuk secrets (`.env` atau secret manager)
- [ ] Enable HTTPS/TLS (sertifikat SSL)
- [ ] Setup Nginx dengan rate limiting
- [ ] Install & configure `django-axes` untuk login protection
- [ ] Run `python manage.py collectstatic --noinput`
- [ ] Run `python manage.py migrate` di production DB
- [ ] Setup Celery worker di background
- [ ] Setup logging & monitoring (Sentry / Prometheus)
- [ ] Configure backups untuk database & media files
- [ ] Test throttling limits dengan load testing
- [ ] Setup CDN untuk static files (optional)
- [ ] Monitor queue depth & worker health

---

## Tips Keamanan Tambahan

1. **Database Security:**
   - Gunakan strong password untuk DB credentials
   - Restrict network access ke DB (private network / firewall)

2. **File Upload Security:**
   - Simpan uploaded files di direktori terpisah dari code (MEDIA_ROOT)
   - Setup virus scanning (ClamAV) untuk uploaded files
   - Jangan serve user-uploaded files sebagai executable (Content-Disposition: attachment)

3. **API Security:**
   - Gunakan CORS policy yang ketat
   - Enable CSRF protection (sudah default di Django)
   - Validate & sanitize semua user input
   - Limit request body size

4. **Celery Security:**
   - Gunakan auth/TLS untuk broker (Redis/RabbitMQ)
   - Monitor queue depth & worker status
   - Set reasonable timeouts untuk tasks
   - Jangan expose broker ports ke publik

5. **Monitoring & Alerting:**
   - Setup real-time alerting untuk errors & throttle hits
   - Monitor CPU, memory, disk usage
   - Track response times & throughput
   - Audit log untuk admin actions

---

## Referensi

- Django Security: https://docs.djangoproject.com/en/5.2/topics/security/
- DRF Throttling: https://www.django-rest-framework.org/api-guide/throttling/
- django-axes: https://django-axes.readthedocs.io/
- Nginx Rate Limiting: https://nginx.org/en/docs/http/ngx_http_limit_req_module.html
- OWASP Top 10: https://owasp.org/www-project-top-ten/

