#!/bin/bash

# Script para executar o detector de fraudes
# Uso: bash executar.sh

echo "=========================================="
echo "DETECTOR DE FRAUDES EMPRESARIAIS"
echo "=========================================="
echo ""

# Ativa o ambiente virtual
echo "Ativando ambiente virtual..."
source /home/paulo/projects/main-server/.venv/bin/activate

# Executa o script
echo "Iniciando processamento..."
echo ""
python3 -u main.py 2>&1 | tee fraud_detection.log

echo ""
echo "=========================================="
echo "PROCESSAMENTO FINALIZADO!"
echo "=========================================="
echo ""
echo "Arquivos gerados:"
echo "  - fraud_detection.log (log de execução)"
echo "  - fraud_detection_results.json (todos os resultados)"
echo "  - fraud_news_with_companies.csv (notícias com empresas)"
echo ""
