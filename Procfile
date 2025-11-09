web: gunicorn odontoia.wsgi
release: python manage.py migrate && python manage.py createsuperuser --noinput --username=admin --email=admin@odontoia.com.br
