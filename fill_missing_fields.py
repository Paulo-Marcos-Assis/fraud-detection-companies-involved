#!/usr/bin/env python3
"""
Preenche os campos title, url e text vazios no CSV
usando os arquivos JSON originais
"""

import json
import csv
import sys
from pathlib import Path

def fill_missing_fields(csv_input=None, csv_output=None):
    """Preenche title, url e text do CSV com dados dos JSONs originais"""
    
    # Permitir passar arquivos como argumentos ou usar padrões
    if csv_input is None:
        csv_input = "/home/paulo/projects/main-server/.PAULO/fraud_news_with_companies.csv"
    if csv_output is None:
        csv_output = csv_input.replace('.csv', '_COMPLETE.csv')
    
    json_dir = "/home/paulo/projects/main-server/.PAULO/983json"
    
    print(f"🔍 Lendo CSV: {csv_input}...")
    
    csv_path = Path(csv_input)
    if not csv_path.exists():
        print(f"❌ Arquivo {csv_input} não encontrado!")
        return
    
    # Ler CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"✓ {len(rows)} notícias encontradas no CSV")
    print("\n📂 Preenchendo campos vazios (title, url, text) com dados dos JSONs originais...\n")
    
    json_path = Path(json_dir)
    filled_title = 0
    filled_url = 0
    filled_text = 0
    errors = 0
    
    for i, row in enumerate(rows, 1):
        filename = row['file']
        needs_filling = False
        
        # Verificar quais campos precisam ser preenchidos
        if not row.get('title') or not row.get('url') or not row.get('text'):
            needs_filling = True
        
        if not needs_filling:
            continue
        
        # Buscar JSON original
        json_file = json_path / filename
        
        if not json_file.exists():
            print(f"⚠ [{i}/{len(rows)}] JSON não encontrado: {filename}")
            errors += 1
            continue
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
            
            # Preencher campos vazios
            if not row.get('title'):
                row['title'] = news_data.get('title', '')
                filled_title += 1
            if not row.get('url'):
                row['url'] = news_data.get('url', '')
                filled_url += 1
            if not row.get('text'):
                row['text'] = news_data.get('text', '')
                filled_text += 1
            
            if (i % 50 == 0):
                print(f"  Processadas: {i}/{len(rows)} notícias...")
            
        except Exception as e:
            print(f"❌ [{i}/{len(rows)}] Erro ao processar {filename}: {e}")
            errors += 1
    
    print(f"\n{'='*70}")
    print(f"PREENCHIMENTO CONCLUÍDO")
    print(f"{'='*70}")
    print(f"Campos title preenchidos: {filled_title}")
    print(f"Campos url preenchidos: {filled_url}")
    print(f"Campos text preenchidos: {filled_text}")
    print(f"Erros: {errors}")
    print(f"{'='*70}\n")
    
    # Salvar CSV atualizado
    output_path = Path(csv_output)
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        # Manter todas as colunas do CSV original
        if rows:
            fieldnames = list(rows[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
    
    print(f"✅ CSV COMPLETO SALVO!")
    print(f"Arquivo: {csv_output}")
    print(f"Total de linhas: {len(rows)}")
    print(f"\n{'='*70}")

if __name__ == "__main__":
    # Permitir passar arquivo CSV como argumento
    if len(sys.argv) > 1:
        csv_input = sys.argv[1]
        csv_output = sys.argv[2] if len(sys.argv) > 2 else None
        fill_missing_fields(csv_input, csv_output)
    else:
        # Usar arquivo padrão
        fill_missing_fields()
