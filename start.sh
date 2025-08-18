#!/bin/bash
set -e

echo "🚀 Iniciando aplicação no Fly.io"
echo "📌 Data e hora atual: $(date)"
echo "📌 Diretório atual: $(pwd)"
echo "📌 Listando arquivos: $(ls -la)"
echo "📌 Verificando variáveis de ambiente: PORT=${PORT}"

export PORT=${PORT:-8000}

echo "🔄 Iniciando o servidor na porta ${PORT}..."

python -m uvicorn api:app --host 0.0.0.0 --port ${PORT} --log-level debug