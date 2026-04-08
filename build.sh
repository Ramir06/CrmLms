#!/usr/bin/env bash
set -o errexit

cd crm_lms
pip install -r requirements.txt
python manage.py collectstatic --no-input --settings=config.settings.prod
python manage.py migrate --settings=config.settings.prod
