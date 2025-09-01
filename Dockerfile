FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar todas as dependências do AutoU (incluindo cors-headers)
RUN pip install \
    Django==5.2.5 \
    djangorestframework==3.14.0 \
    drf-spectacular==0.27.0 \
    django-cors-headers==4.3.1 \
    psycopg2-binary==2.9.7 \
    gunicorn==21.2.0 \
    whitenoise==6.6.0 \
    scikit-learn==1.3.0 \
    pandas==2.1.1 \
    numpy==1.24.3 \
    Pillow==10.0.1 \
    python-decouple==3.8

COPY . .

ENV DJANGO_SETTINGS_MODULE=core.settings.docker
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
