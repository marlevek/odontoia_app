#!/bin/bash

echo "🚀 Iniciando o OdontoIA..."

# Função para testar a conexão com o banco via Python puro
check_db() {
  python <<END
import psycopg2, os, sys
try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        connect_timeout=3
    )
    conn.close()
except Exception as e:
    sys.exit(1)
END
}

# Aguarda o PostgreSQL estar pronto
echo "⏳ Aguardando banco de dados..."
until check_db; do
  echo "🔄 Banco ainda não está pronto... aguardando 3s"
  sleep 3
done

echo "✅ Banco pronto, aplicando migrações..."
python manage.py migrate --noinput

echo "📦 Coletando arquivos estáticos..."
python manage.py collectstatic --noinput

echo "💼 Iniciando o servidor Gunicorn..."
gunicorn odontoia.wsgi:application --bind 0.0.0.0:$PORT
