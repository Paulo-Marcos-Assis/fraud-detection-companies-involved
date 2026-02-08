# Fraud Detection Companies Involved 

Este projeto processa 983 notícias de portais brasileiros para identificar casos de fraude empresarial, extraindo informações estruturadas como:

- Tipos de fraude
- Empresas envolvidas
- Pessoas envolvidas (com seus papéis/funções)
- Nível de confiança da detecção
- Tempo de processamento


### Pré-requisitos

```bash
pip install -r requirements.txt
```

### Configuração

O script usa o servidor Ollama para inferência LLM. Configure as variáveis de ambiente:

```bash
export OLLAMA_HOST="https://ollama-dev.ceos.ufsc.br"
export OLLAMA_MODEL="gpt-oss:20b"
```

```bash
# Executar script principal
bash executar.sh

# Ou manualmente
python3 main.py

```bash
# Ver logs em tempo real
tail -f fraud_detection.log

# Verificar se está rodando
ps aux | grep "python3.*main.py"
```

## Arquivos Gerados

- `fraud_detection_results.json` - Resultados completos em JSON
- `fraud_news_with_companies_COMPLETE.csv` - CSV com notícias que mencionam empresas
- `performance_metrics.json` - Métricas de performance
- `fraud_detection.log` - Log de execução

## Scripts Auxiliares

### `fill_missing_fields.py`
Preenche campos vazios (title, url, text) no CSV usando os JSONs originais.

```bash
python3 fill_missing_fields.py
```

### `extract_from_log.py`
Extrai resultados parciais do log quando o script é interrompido.

```bash
python3 extract_from_log.py
```

### `extract_partial_csv.py`
Extrai CSV de resultados parciais do JSON.

```bash
python3 extract_partial_csv.py
```

## Configurações

### Parâmetros Principais (main.py)

- `TIMEOUT_SECONDS = 180` - Timeout por notícia (3 minutos)
- `START_FROM = 434` - Começar da notícia N (pular anteriores)
- `SAVE_INTERVAL = 25` - Salvar a cada N notícias

### Estrutura do Prompt

O prompt instrui o LLM a:
1. Identificar se a notícia trata de fraude empresarial
2. Classificar o nível de confiança (alta/média/baixa)
3. Extrair tipos de fraude
4. Identificar empresas envolvidas
5. Identificar pessoas envolvidas com seus papéis
6. Diferenciar claramente empresas de pessoas

## Estrutura de Dados

### CSV de Saída
```csv
file,title,url,text,companies,people,fraud_types,confidence,execution_time_seconds
noticia_0001.json,"Título","URL","Texto","Empresa A; Empresa B","João Silva (empresário); Maria Costa (prefeita)","fraude em licitação; corrupção",alta,5.23
```

## Metodologia

O sistema usa um LLM (Large Language Model) para análise semântica das notícias, identificando padrões de fraude empresarial através de:

1. **Análise contextual** do texto completo
2. **Extração de entidades** nomeadas (empresas e pessoas)
3. **Classificação de tipos de fraude** baseada em taxonomia pré-definida
4. **Avaliação de confiança** baseada na clareza das evidências no texto

## Licença

Este projeto é parte de pesquisa acadêmica da UFSC.
