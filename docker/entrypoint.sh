#!/bin/bash
# Docker entrypoint — executa migrações e coleta estáticos antes de subir o servidor
set -e

echo "==> Aguardando banco de dados..."
python -c "
import time, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', '${DJANGO_SETTINGS_MODULE:-config.settings.production}')
django.setup()
from django.db import connection
for attempt in range(30):
    try:
        connection.ensure_connection()
        print('Banco de dados disponível.')
        break
    except Exception as e:
        print(f'Tentativa {attempt+1}/30: {e}')
        time.sleep(2)
else:
    print('ERRO: Banco de dados não disponível após 30 tentativas.')
    exit(1)
"

echo "==> Executando migrações..."
python manage.py migrate --noinput

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "==> Iniciando servidor..."
exec "$@"
