#!/bin/bash
echo "Applying database migrations..."
python manage.py migrate --noinput
gunicorn --bind 0.0.0.0:13912 app.wsgi