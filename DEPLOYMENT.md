# CV Screening - Deployment & Security Guide

Panduan lengkap untuk menjalankan, mengamankan, dan melakukan load testing CV Screening application.

## Quick Start (Development)

### 1. Setup Lingkungan

```bash
# Clone repository
git clone <repo-url>
cd cv-screening-master

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# atau (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env dengan credentials Anda
```

### 2. Database & Migrations

```bash
# Jalankan migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 3. Development Server

Terminal 1: Django
```bash
python manage.py runserver
```

Terminal 2: Celery Worker (optional)
```bash
celery -A cv_screening worker --loglevel=info
```

Terminal 3: Redis Server (optional, untuk Celery)
```bash
redis-server
```

Akses aplikasi di: http://localhost:8000

---

## Testing

### Unit Tests

```bash
# Jalankan semua tests
python manage.py test

# Jalankan test spesifik
python manage.py test api.tests.UploadViewThrottleTests
python manage.py test api.tests.FileUploadValidationTests

# Dengan coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Manual Testing Throttling

```bash
# Test upload throttle (5/minute limit)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/upload/ \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -F "file=@test.pdf"
  echo "Request $i"
done
# Permintaan ke-6 harus return 429 (Too Many Requests)

# Test evaluate throttle (2/minute limit)
for i in {1..3}; do
  curl -X POST http://localhost:8000/api/evaluate/ \
    -H "Authorization: Bearer YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"job_title":"Test","cv_id":"550e8400-e29b-41d4-a716-446655440000","project_report_id":"550e8400-e29b-41d4-a716-446655440001"}'
  echo "Request $i"
done
# Permintaan ke-3 harus return 429
```

### Load Testing (Locust)

```bash
# Install locust
pip install locust

# Run load test
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10

# Buka browser ke http://localhost:8089
# Monitor metrics & throttle hits

# Run in headless mode
locust -f locustfile.py --host=http://localhost:8000 \
  --users 100 --spawn-rate 10 --run-time 5m --headless
```

---

## Production Deployment

### 1. Environment Setup

```bash
# Copy .env.example ke .env dengan production values
cp .env.example .env

# Generate strong SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
# Masukkan hasilnya ke SECRET_KEY di .env
```

### 2. Install & Configure Nginx

**Linux:**
```bash
# Install nginx
sudo apt-get update
sudo apt-get install nginx

# Copy config
sudo cp nginx-config.example /etc/nginx/sites-available/cv-screening

# Edit untuk domain & paths
sudo nano /etc/nginx/sites-available/cv-screening

# Enable site
sudo ln -s /etc/nginx/sites-available/cv-screening /etc/nginx/sites-enabled/

# Test config
sudo nginx -t

# Reload
sudo systemctl reload nginx
```

**SSL Certificate (Let's Encrypt):**
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### 3. Setup Gunicorn + Supervisor

```bash
# Install gunicorn
pip install gunicorn

# Create systemd service: /etc/systemd/system/cv-screening.service
[Unit]
Description=CV Screening Django Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/cv-screening-master
ExecStart=/path/to/venv/bin/gunicorn \
  --workers 4 \
  --bind 127.0.0.1:8000 \
  --timeout 120 \
  cv_screening.wsgi:application
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable & start
sudo systemctl enable cv-screening
sudo systemctl start cv-screening
sudo systemctl status cv-screening
```

### 4. Setup Celery Worker (Systemd)

```bash
# Create /etc/systemd/system/celery-worker.service
[Unit]
Description=Celery Worker for CV Screening
After=network.target redis.service

[Service]
Type=forking
User=www-data
WorkingDirectory=/path/to/cv-screening-master
ExecStart=/path/to/venv/bin/celery -A cv_screening worker \
  --loglevel=info \
  --logfile=/var/log/celery/worker.log \
  --pidfile=/var/run/celery/worker.pid

[Install]
WantedBy=multi-user.target

# Enable & start
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown www-data:www-data /var/log/celery /var/run/celery
sudo systemctl enable celery-worker
sudo systemctl start celery-worker
```

### 5. Database Backup & Maintenance

```bash
# PostgreSQL backup (jika menggunakan PostgreSQL)
pg_dump -U username dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# Regular backups dengan cron
0 2 * * * pg_dump -U username dbname > /backups/db_$(date +\%Y\%m\%d).sql
```

### 6. Monitoring & Logs

```bash
# Tail application logs
sudo tail -f /var/log/django/app.log

# Tail celery logs
sudo tail -f /var/log/celery/worker.log

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Monitor system resources
watch -n 1 'ps aux | grep celery'
watch -n 1 'ps aux | grep gunicorn'
```

---

## Security Checklist

- [ ] DEBUG = False di production
- [ ] SECRET_KEY dipindahkan ke .env (bukan hardcoded)
- [ ] Database credentials di .env
- [ ] HTTPS/SSL configured (Let's Encrypt)
- [ ] SECURE_SSL_REDIRECT = True
- [ ] HSTS headers enabled (SECURE_HSTS_SECONDS)
- [ ] Rate limiting enabled (DRF + Nginx)
- [ ] django-axes configured (login protection)
- [ ] File upload validation enabled
- [ ] Celery worker runs with limited privileges
- [ ] Redis/RabbitMQ secured (auth + TLS)
- [ ] Logging & monitoring configured
- [ ] Regular backups scheduled
- [ ] Firewall rules configured (block non-essential ports)
- [ ] Regular security updates

---

## Performance Tuning

### DRF Throttle Limits (Adjust if needed)

File: `cv_screening/settings.py`
```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',      # anonymous users
        'user': '200/minute',     # authenticated users
        'upload_cv': '5/minute',  # file uploads
        'start_evaluation': '2/minute',  # evaluation jobs
    }
}
```

### Nginx Rate Limiting (Adjust if needed)

File: `nginx-config.example`
```nginx
limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=10r/s;  # 10 requests/second
limit_req zone=upload_limit burst=5 nodelay;  # Allow burst of 5
```

### Celery Task Config

File: `evaluations/tasks.py`
```python
@shared_task(rate_limit='5/m', time_limit=300)  # 5/min, 5-min timeout
def evaluate_documents(job_id):
    ...
```

Adjust based on:
- Server capacity
- User base size
- Expected traffic patterns

---

## Troubleshooting

### Issue: 429 Too Many Requests on normal usage

**Solution:**
- Check current rate limits in settings
- Increase limits if acceptable for your use case
- Verify client isn't making duplicate requests

### Issue: File upload fails with 413 Payload Too Large

**Solution:**
- Increase `FILE_UPLOAD_MAX_MEMORY_SIZE` in settings
- Check nginx `client_max_body_size` limit

### Issue: Celery tasks not running

**Solution:**
- Check Redis connection: `redis-cli ping`
- Check worker logs: `sudo journalctl -u celery-worker -f`
- Verify Celery config in `cv_screening/settings.py`

### Issue: django-axes locks out legitimate users

**Solution:**
- Adjust `AXES_FAILURE_LIMIT` & `AXES_COOLOFF_DURATION`
- Unlock user: `python manage.py axes_list` then `python manage.py axes_reset`

---

## References

- Django Security: https://docs.djangoproject.com/en/5.2/topics/security/
- DRF Documentation: https://www.django-rest-framework.org/
- django-axes: https://django-axes.readthedocs.io/
- Nginx: https://nginx.org/en/
- Celery: https://docs.celeryproject.org/

