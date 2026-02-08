# 📖 GUIA DE COMANDOS - Detecção de Fraudes

## 🔍 Acompanhar Logs em Tempo Real

### Ver o log enquanto o script executa:
```bash
tail -f fraud_detection.log
```
**Explicação:** O comando `tail -f` mostra as últimas linhas do arquivo e continua atualizando conforme novas linhas são adicionadas.

**Para sair:** Pressione `Ctrl+C`

### Ver as últimas 50 linhas do log:
```bash
tail -50 fraud_detection.log
```

### Ver as primeiras 50 linhas do log:
```bash
head -50 fraud_detection.log
```

### Buscar uma palavra específica no log:
```bash
grep "FRAUDE DETECTADA" fraud_detection.log
```

### Contar quantas fraudes foram detectadas:
```bash
grep -c "FRAUDE DETECTADA" fraud_detection.log
```

---

## ⚙️ Verificar se o Script Está Rodando

```bash
ps aux | grep "python3.*main.py"
```

Se aparecer uma linha com `python3 main.py`, o script está rodando.

---

## 🛑 Parar o Script

### Método 1 - Se você iniciou no terminal:
```bash
# Pressione Ctrl+C
```

### Método 2 - Se está em background:
```bash
# Encontre o PID:
ps aux | grep "python3.*main.py"

# Mate o processo (substitua 12345 pelo PID real):
kill 12345

# Se não funcionar:
kill -9 12345
```

---

## 📊 Verificar Progresso

### Ver quantas notícias já foram processadas:
```bash
grep -c "Processando:" fraud_detection.log
```

### Ver o arquivo de resultados (se já foi criado):
```bash
cat fraud_detection_results.json | head -50
```

### Ver o tamanho do arquivo de resultados:
```bash
ls -lh fraud_detection_results.json
```

---

## 🚀 Executar o Script

### Forma básica (vê tudo no terminal):
```bash
cd /home/paulo/projects/main-server/.PAULO
source /home/paulo/projects/main-server/.venv/bin/activate
python3 main.py
```

### Forma com log em arquivo (recomendado):
```bash
cd /home/paulo/projects/main-server/.PAULO
source /home/paulo/projects/main-server/.venv/bin/activate
python3 -u main.py 2>&1 | tee fraud_detection.log
```

### Forma em background (continua mesmo se fechar o terminal):
```bash
cd /home/paulo/projects/main-server/.PAULO
source /home/paulo/projects/main-server/.venv/bin/activate
nohup python3 -u main.py > fraud_detection.log 2>&1 &
```

**Para ver o log depois:**
```bash
tail -f fraud_detection.log
```

---

## 📁 Navegar entre Pastas

```bash
# Ver onde você está:
pwd

# Ir para a pasta do projeto:
cd /home/paulo/projects/main-server/.PAULO

# Listar arquivos na pasta atual:
ls -lh

# Voltar para a pasta anterior:
cd ..
```

---

## 🔧 Comandos Úteis do Python

### Verificar se o ambiente virtual está ativo:
```bash
which python3
# Deve mostrar: /home/paulo/projects/main-server/.venv/bin/python3
```

### Ativar o ambiente virtual:
```bash
source /home/paulo/projects/main-server/.venv/bin/activate
```

### Desativar o ambiente virtual:
```bash
deactivate
```

### Instalar pacotes:
```bash
pip install nome-do-pacote
```

---

## 💡 Dicas Importantes

1. **Sempre ative o ambiente virtual antes de executar o script**
2. **Use `Ctrl+C` para interromper processos no terminal**
3. **Use `tail -f` para acompanhar logs em tempo real**
4. **Use `nohup` se quiser que o script continue rodando mesmo depois de fechar o terminal**
