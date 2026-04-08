#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
cd crm_lms
python manage.py collectstatic --no-input --settings=config.settings.prod

if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL is not set — skipping migrations during build."
    echo "Migrations will run automatically on container start via the start command."
else
    python manage.py migrate --settings=config.settings.prod
fi
