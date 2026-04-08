web: cd crm_lms && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
web: cd crm_lms && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --log-level debug
