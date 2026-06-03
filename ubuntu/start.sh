#!/usr/bin/env bash

# Start the Django Web Server in the background
cd /app/django-backend
python manage.py runserver 0.0.0.0:8000 &

# Start the Refund Worker in the background
python manage.py run_refund_server &

# Start the Scheduler in the background
cd /app/scheduler-backend
python main.py &

# Wait for ANY of the background processes to exit
wait -n

# Exit with the status of the process that failed
exit $?
