# 📊 Guia: Processamento Dataset NDMais

## 🎯 Objetivo

Processar mais de 190.000 notícias do portal NDMais para identificar fraudes empresariais, começando do JSON 30000.

---

## 📁 Estrutura de Diretórios

```
.PAULO/
├── dataset_building/
│   └── ndmais_articles_json/     # ← Pasta com 190k+ JSONs
│       ├── noticia_00001.json
│       ├── noticia_00002.json
│       ├── ...
│       └── noticia_190000+.json
├── main.py                        # Script principal (modificado)
├── run_ndmais_dataset.sh         # Script de execução
└── fraud_detection_ndmais.log    # Log de execução
```

---

## 🔧 Configurações do Script

### **Parâmetros Principais** (`main.py`)

```python
START_FROM = 30000                    # Começa do JSON 30000
TIMEOUT_SECONDS = 180                 # 3 minutos por notícia
MAX_CONSECUTIVE_403_ERRORS = 5        # Para após 5 erros 403 seguidos
SAVE_INTERVAL = 25                    # Salva a cada 25 notícias
```

### **Proteção Contra Erro 403**

O script agora detecta erros 403 do Ollama e:
- ✅ **Tolera erros esporádicos** (continua processando)
- ✅ **Reseta contador** quando uma notícia é processada com sucesso
- ⚠️ **Para automaticamente** após 5 erros 403 **consecutivos**
- 💾 **Salva progresso** antes de parar

---

## 🚀 Como Executar

### **Passo 1: Transferir Pasta do Windows**

Você precisa transferir a pasta `ndmais_articles_json` do Windows para o servidor Linux.

#### **Opção A: SCP (PowerShell no Windows)**

```powershell
cd "C:\Users\plogs\OneDrive\Documentos\C O D E\2026\fraud-detection-companies-involved"

scp -r "dataset_building\ndmais_articles_json" paulo@ceoss:/home/paulo/projects/main-server/.PAULO/dataset_building/
```

#### **Opção B: WinSCP (Interface Gráfica)**
1. Baixe WinSCP: https://winscp.net/
2. Conecte ao servidor `ceoss`
3. Navegue até `/home/paulo/projects/main-server/.PAULO/`
4. Crie pasta `dataset_building`
5. Arraste `ndmais_articles_json` para dentro

#### **Opção C: Compactar e Transferir**
```powershell
# No Windows
Compress-Archive -Path "dataset_building\ndmais_articles_json" -DestinationPath "ndmais.zip"
scp "ndmais.zip" paulo@ceoss:/home/paulo/projects/main-server/.PAULO/
```

```bash
# No Linux
cd /home/paulo/projects/main-server/.PAULO
unzip ndmais.zip
```

---

### **Passo 2: Executar Processamento**

```bash
cd /home/paulo/projects/main-server/.PAULO

# Opção 1: Usar script automatizado
bash run_ndmais_dataset.sh

# Opção 2: Executar manualmente
python3 main.py
```

---

## 📊 Acompanhamento em Tempo Real

### **Ver Logs**

```bash
# Acompanhar processamento em tempo real
tail -f fraud_detection_ndmais.log

# Ver últimas 50 linhas
tail -50 fraud_detection_ndmais.log

# Buscar erros 403
grep "403" fraud_detection_ndmais.log
```

### **Verificar Progresso**

```bash
# Ver quantas notícias já foram processadas
grep "Processando:" fraud_detection_ndmais.log | wc -l

# Ver última notícia processada
grep "Processando:" fraud_detection_ndmais.log | tail -1

# Ver fraudes detectadas
grep "FRAUDE DETECTADA" fraud_detection_ndmais.log | wc -l
```

### **Verificar se Está Rodando**

```bash
ps aux | grep "python3.*main.py"
```

---

## 🛑 Parar Processamento

```bash
# Encontrar PID do processo
ps aux | grep "python3.*main.py"

# Parar (substitua PID pelo número encontrado)
kill PID
```

---

## 📈 Estimativas

### **Tempo de Processamento**

- **Por notícia:** ~2-3 segundos (média)
- **190.000 notícias:** ~105-158 horas (~4-7 dias)
- **Do JSON 30000 ao final (160.000):** ~88-133 horas (~3-5 dias)

### **Tamanho dos Arquivos**

- **JSON de entrada:** ~190.000 arquivos
- **JSON de saída:** ~10-50 MB (dependendo de quantas fraudes)
- **CSV final:** ~5-20 MB

---

## 🔄 Retomar Processamento

Se o script parar (erro 403, timeout, etc), ele salva o progresso automaticamente.

Para retomar:

```bash
# O script detecta automaticamente onde parou
python3 main.py
```

Se quiser forçar começar de um número específico, edite `main.py`:

```python
START_FROM = 50000  # Exemplo: começar do 50000
```

---

## 📁 Arquivos Gerados

| Arquivo | Descrição |
|---------|-----------|
| `fraud_detection_ndmais_results.json` | Resultados completos (todas as fraudes) |
| `fraud_news_ndmais_with_companies.csv` | CSV com fraudes que mencionam empresas |
| `performance_metrics_ndmais.json` | Métricas de performance |
| `fraud_detection_ndmais.log` | Log completo de execução |

---

## ⚠️ Tratamento de Erros

### **Erro 403 do Ollama**

**Sintoma:**
```
[❌ ERRO 403] Ollama retornou erro de permissão
⚠️  Erro 403 consecutivo #1/5
```

**O que acontece:**
- Script tolera até 4 erros consecutivos
- No 5º erro consecutivo, **para automaticamente**
- Salva progresso antes de parar
- Você pode retomar depois

**Solução:**
1. Aguarde alguns minutos
2. Execute novamente: `python3 main.py`
3. Script retoma de onde parou

### **Timeout (180s)**

**Sintoma:**
```
[⏱️ TIMEOUT] Processamento excedeu 180s - pulando notícia
```

**O que acontece:**
- Notícia é pulada
- Processamento continua normalmente

**Solução:**
- Normal para notícias muito longas
- Não requer ação

---

## 🔍 Verificar Qualidade dos Resultados

```bash
# Ver exemplos de fraudes detectadas
grep -A 3 "FRAUDE DETECTADA" fraud_detection_ndmais.log | head -20

# Contar por nível de confiança
grep "confiança: alta" fraud_detection_ndmais.log | wc -l
grep "confiança: média" fraud_detection_ndmais.log | wc -l
grep "confiança: baixa" fraud_detection_ndmais.log | wc -l

# Ver empresas mais mencionadas
cut -d',' -f5 fraud_news_ndmais_with_companies.csv | sort | uniq -c | sort -rn | head -20
```

---

## 💡 Dicas

1. **Execute em `screen` ou `tmux`** para não perder o processo se desconectar:
   ```bash
   screen -S fraud_detection
   python3 main.py
   # Ctrl+A, D para desconectar
   # screen -r fraud_detection para reconectar
   ```

2. **Monitore uso de recursos:**
   ```bash
   htop  # CPU e memória
   ```

3. **Backup periódico:**
   ```bash
   # A cada 24h, copie os arquivos gerados
   cp fraud_detection_ndmais_results.json backup_$(date +%Y%m%d).json
   ```

---

## 📞 Troubleshooting

### Problema: "Pasta dataset_building não encontrada"
**Solução:** Transfira a pasta do Windows primeiro (ver Passo 1)

### Problema: "Muitos erros 403"
**Solução:** Servidor Ollama pode estar sobrecarregado. Aguarde e tente novamente.

### Problema: Script muito lento
**Solução:** Normal. Processamento de 190k notícias leva dias.

### Problema: Disco cheio
**Solução:** Limpe logs antigos ou mova arquivos grandes para outro local.

---

## 🎯 Próximos Passos Após Processamento

1. ✅ Analisar CSV gerado
2. ✅ Gerar estatísticas
3. ✅ Criar visualizações
4. ✅ Publicar resultados

---

**Boa sorte com o processamento! 🚀**
