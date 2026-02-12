#!/bin/bash

# Script para processar dataset ndmais_articles_json
# Começa do JSON 30000 e processa até o final

echo "=========================================="
echo "Processamento Dataset NDMais"
echo "=========================================="
echo ""
echo "Configurações:"
echo "  - Pasta de entrada: dataset_building/ndmais_articles_json"
echo "  - Começar do JSON: 30000"
echo "  - Timeout por notícia: 180s"
echo "  - Proteção contra erro 403: Para após 5 erros consecutivos"
echo "  - Salvamento automático: A cada 25 notícias"
echo ""
echo "=========================================="
echo ""

# Ativar ambiente virtual se existir
if [ -d "venv" ]; then
    echo "Ativando ambiente virtual..."
    source venv/bin/activate
fi

# Executar script principal
python3 main.py \
    --input-dir "dataset_building/ndmais_articles_json" \
    --output-file "fraud_detection_ndmais_results.json" \
    --csv-file "fraud_news_ndmais_with_companies.csv" \
    --metrics-file "performance_metrics_ndmais.json" \
    2>&1 | tee fraud_detection_ndmais.log

echo ""
echo "=========================================="
echo "Processamento finalizado!"
echo "Verifique os arquivos gerados:"
echo "  - fraud_detection_ndmais_results.json"
echo "  - fraud_news_ndmais_with_companies.csv"
echo "  - performance_metrics_ndmais.json"
echo "  - fraud_detection_ndmais.log"
echo "=========================================="
