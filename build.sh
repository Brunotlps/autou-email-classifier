#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input --settings=core.settings.render

# Run migrations
python manage.py migrate --settings=core.settings.render
