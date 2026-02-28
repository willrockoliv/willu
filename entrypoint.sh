#!/bin/sh
set -e

echo "⏳ Aguardando PostgreSQL..."
until python -c "
import socket, sys, os
url = os.environ.get('DATABASE_URL', '')
# Extrair host:port da URL
parts = url.split('@')[-1].split('/')[0]
host, port = parts.split(':')
s = socket.socket()
try:
    s.settimeout(2)
    s.connect((host, int(port)))
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    echo "  PostgreSQL ainda não disponível, tentando novamente em 1s..."
    sleep 1
done
echo "✅ PostgreSQL disponível!"

echo "🌱 Rodando seed de categorias..."
python -m scripts.seed

echo "🚀 Iniciando Willu..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ${UVICORN_ARGS:-}
