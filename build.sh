#!/usr/bin/env bash
set -o errexit

# Production build script for OkuuTrack Django project
echo "Starting production build..."

# Install dependencies
echo "Installing dependencies..."
pip install -r crm_lms/requirements.txt

# Collect static files
echo "Collecting static files..."
cd crm_lms
python manage.py collectstatic --no-input --settings=config.settings.prod

# Run migrations
echo "Running database migrations..."
python manage.py migrate --settings=config.settings.prod

echo "Production build completed successfully!"
