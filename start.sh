#!/bin/bash

echo "🚀 Iniciando o OdontoIA..."

# Aguarda o PostgreSQL estar pronto (Railway pode demorar 10-15s)
echo "⏳ Aguardando banco de dados..."
until pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 2
done

echo "✅ Banco pronto, aplicando migrações..."
python manage.py migrate --noinput

echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "💼 Iniciando o servidor Gunicorn..."
gunicorn odontoia.wsgi:application --bind 0.0.0.0:$PORT
