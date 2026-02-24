import os
import json
import csv
import time
import signal
from datetime import datetime
from typing import Dict, List
from pathlib import Path
from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://ollama-dev.ceos.ufsc.br")
SELECTED_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
LLM_TEMPERATURE = 0
TIMEOUT_SECONDS = 180  # Timeout de 180 segundos por notícia
START_FROM = 0  # Processar desde o início (jornalconexao - novo dataset)
MAX_CONSECUTIVE_403_ERRORS = 5  # Parar após 5 erros 403 consecutivos

class TimeoutError(Exception):
    """Exceção lançada quando o processamento excede o timeout"""
    pass

class OllamaError403(Exception):
    """Exceção lançada quando Ollama retorna erro 403"""
    pass

def timeout_handler(signum, frame):
    """Handler para timeout"""
    raise TimeoutError("Processamento excedeu o tempo limite")

class FraudDetector:
    def __init__(self):
        print(f"Fraud Detector configurado para usar Ollama em {OLLAMA_HOST} (modelo: {SELECTED_MODEL})")
        self.llm = None
        self._llm_initialized = False
    
    def _ensure_llm(self):
        if not self._llm_initialized:
            print(f"Conectando ao Ollama em {OLLAMA_HOST}...")
            try:
                self.llm = ChatOllama(
                    model=SELECTED_MODEL,
                    base_url=OLLAMA_HOST,
                    temperature=LLM_TEMPERATURE,
                    timeout=120
                )
                self._llm_initialized = True
                print("Conexão com Ollama estabelecida com sucesso!")
            except Exception as e:
                print(f"ERRO ao conectar ao Ollama: {e}")
                self.llm = None
                self._llm_initialized = True

    def analyze_fraud(self, text: str, title: str, timeout: int = TIMEOUT_SECONDS) -> Dict:
        """
        Analisa se a notícia trata de fraudes envolvendo empresas.
        
        Retorna:
        {
            "is_fraud_related": bool,
            "confidence": str,  # "alta", "média", "baixa"
            "fraud_types": List[str],
            "companies_involved": List[str],
            "summary": str
        }
        """
        default_return = {
            "is_fraud_related": False,
            "confidence": "baixa",
            "fraud_types": [],
            "companies_involved": [],
            "people_involved": [],
            "execution_time_seconds": 0.0
        }
        
        self._ensure_llm()
        
        if not self.llm:
            print("Erro: LLM não inicializado.")
            return default_return
        
        if not text or not isinstance(text, str):
            return default_return

        full_text = f"{title}\n\n{text}" if title else text
        
        prompt_content = f"""
Você é um especialista em análise de notícias sobre fraudes empresariais e crimes contra a administração pública.

Sua tarefa é analisar a notícia fornecida e determinar se ela trata de fraudes envolvendo empresas.

----------------------------------------------------------------------
INSTRUÇÕES:

1. Leia atentamente e COMPLETAMENTE todo o texto da notícia, do início ao fim. Não analise apenas trechos iniciais ou finais - processe o texto inteiro para garantir uma análise precisa.

2. Identifique se a notícia trata de FRAUDES EMPRESARIAIS, incluindo mas não limitado a:
   - Fraude em licitações
   - Cartel entre empresas
   - Superfaturamento
   - Corrupção envolvendo empresas
   - Lavagem de dinheiro empresarial
   - Formação de organização criminosa empresarial
   - Contratos fraudulentos
   - Simulação de concorrência
   - Direcionamento de licitações
   - Pagamento de propina por empresas
   - Desvio de recursos públicos envolvendo empresas
   - Falsificação de documentos em processos licitatórios
   - Qualquer outro tipo de fraude que envolva empresas

3. Identifique o nível de confiança da análise:
   - "alta": A notícia claramente trata de fraude empresarial com detalhes explícitos
   - "média": A notícia provavelmente trata de fraude empresarial mas com alguns detalhes implícitos
   - "baixa": A notícia menciona fraude de forma tangencial ou não está claro

4. Liste os TIPOS DE FRAUDE identificados (exemplos: "fraude em licitação", "cartel", "superfaturamento", etc.)

5. Liste as EMPRESAS mencionadas:
   - APENAS extraia nomes de PESSOAS JURÍDICAS (empresas, razões sociais)
   - Indicadores de empresa: Ltda., S.A., ME, EPP, EIRELI, palavras como "Construtora", "Serviços", "Comércio", "Engenharia", "Locações", etc.
   - NÃO inclua nomes de pessoas físicas aqui
   - Exemplos de EMPRESAS: "Tendas Catarinense Locações Ltda.", "Triângulo Engenharia e Consultoria", "Construtora ABC Ltda."
   - Exemplos que NÃO são empresas: "João Silva", "Maria Santos", "Pedro Oliveira"

6. Liste as PESSOAS ENVOLVIDAS mencionadas COM SEUS PAPÉIS/FUNÇÕES:
   - APENAS extraia nomes de PESSOAS FÍSICAS (empresários, políticos, servidores públicos, etc.)
   - IMPORTANTE: Inclua o papel/função da pessoa entre parênteses após o nome
   - Formato: "Nome Completo (função/papel)"
   - Indicadores de pessoa: nomes próprios seguidos de sobrenomes, sem sufixos empresariais
   - Analise o contexto para identificar quem é a pessoa (empresário, prefeito, servidor, sócio, etc.)
   - NÃO inclua razões sociais ou nomes de empresas aqui
   - Exemplos CORRETOS: 
     * "João Silva (empresário)"
     * "Pedro Costa (prefeito)"
     * "Maria Santos (sócia da empresa)"
     * "Carlos Oliveira (servidor público)"
     * "Ana Lima (ex-prefeita)"
   - Exemplos INCORRETOS: 
     * "João Silva" (falta o papel)
     * "Construtora Silva Ltda." (é empresa, não pessoa)

IMPORTANTE - DIFERENCIAÇÃO:
- Se aparecer "Ltda.", "S.A.", "ME", "EPP", "EIRELI" → é EMPRESA
- Se for apenas nome e sobrenome de pessoa → é PESSOA
- Se o texto menciona "o empresário [nome]", "o prefeito [nome]", "o servidor [nome]" → é PESSOA
- Se o texto menciona "a empresa [nome]", "a construtora [nome]" → é EMPRESA
- Em caso de dúvida, analise o contexto ao redor do nome no texto

----------------------------------------------------------------------
FORMATO DE RESPOSTA:

Retorne APENAS um JSON válido no formato:

{{
  "is_fraud_related": true ou false,
  "confidence": "alta" ou "média" ou "baixa",
  "fraud_types": ["tipo1", "tipo2", ...],
  "companies_involved": ["empresa1", "empresa2", ...],
  "people_involved": ["pessoa1", "pessoa2", ...]
}}

IMPORTANTE:
- Se a notícia NÃO trata de fraude empresarial, retorne is_fraud_related: false e listas vazias
- Seja preciso e extraia apenas informações explícitas no texto
- Não invente ou infira informações que não estão no texto

----------------------------------------------------------------------
Texto da notícia:
\"\"\"{full_text}\"\"\"

Responda APENAS com o JSON válido, sem texto adicional.
"""

        start_time = time.time()
        
        # Configurar timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt_content)])
            signal.alarm(0)  # Cancelar timeout se completou
            result = response.content.strip()
            parsed_result = self._parse_json_response(result, default_return)
            execution_time = time.time() - start_time
            parsed_result["execution_time_seconds"] = round(execution_time, 2)
            return parsed_result
        except TimeoutError:
            signal.alarm(0)  # Cancelar timeout
            print(f"[⏱️ TIMEOUT] Processamento excedeu {timeout}s - pulando notícia")
            execution_time = time.time() - start_time
            default_return["execution_time_seconds"] = round(execution_time, 2)
            return default_return
        except Exception as e:
            signal.alarm(0)  # Cancelar timeout
            error_msg = str(e)
            # Verificar se é erro 403
            if "403" in error_msg or "Forbidden" in error_msg:
                print(f"[❌ ERRO 403] Ollama retornou erro de permissão: {error_msg}")
                raise OllamaError403(f"Erro 403 do Ollama: {error_msg}")
            print(f"[Erro na Análise] {e}")
            execution_time = time.time() - start_time
            default_return["execution_time_seconds"] = round(execution_time, 2)
            return default_return

    def _parse_json_response(self, result_str: str, default_return: Dict) -> Dict:
        if result_str.startswith("```json"):
            result_str = result_str[7:]
        if result_str.startswith("```"):
            result_str = result_str[3:]
        if result_str.endswith("```"):
            result_str = result_str[:-3]
        
        result_str = result_str.strip()

        try:
            data = json.loads(result_str)
            
            out = {
                "is_fraud_related": bool(data.get("is_fraud_related", False)),
                "confidence": data.get("confidence", "baixa"),
                "fraud_types": [],
                "companies_involved": [],
                "people_involved": [],
                "execution_time_seconds": 0.0
            }
            
            for key in ["fraud_types", "companies_involved", "people_involved"]:
                value = data.get(key, [])
                if isinstance(value, str):
                    value = [value] if value.strip() else []
                elif not isinstance(value, list):
                    value = []
                
                clean_list = []
                seen = set()
                for item in value:
                    s = str(item).strip().strip('"').strip("'").strip()
                    if s and s not in seen:
                        clean_list.append(s)
                        seen.add(s)
                
                out[key] = clean_list
            
            return out
        except json.JSONDecodeError:
            print(f"Falha ao decodificar JSON. Início da resposta: {result_str[:50]}...")
            return default_return


def save_csv_incremental(csv_file: str, fraud_news_with_companies: list):
    """
    Salva o CSV incrementalmente com os resultados atuais.
    """
    csv_path = Path(csv_file)
    if fraud_news_with_companies:
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['file', 'title', 'url', 'text', 'companies', 'people', 'fraud_types', 'confidence', 'execution_time_seconds']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(fraud_news_with_companies)


def get_already_processed_files(output_file: str) -> set:
    """
    Retorna conjunto de arquivos já processados do JSON parcial.
    """
    output_path = Path(output_file)
    if not output_path.exists():
        return set()
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        fraud_news = data.get('fraud_news', [])
        return {entry['file'] for entry in fraud_news}
    except:
        return set()


def process_all_news(input_dir: str, output_file: str, csv_file: str, metrics_file: str, resume: bool = True):
    """
    Processa todas as notícias na pasta e identifica aquelas relacionadas a fraudes.
    Gera um CSV com apenas as notícias que têm empresas envolvidas em fraudes.
    Gera um arquivo de métricas de performance separado.
    Salva incrementalmente a cada 25 notícias processadas.
    Inclui timeout de 60s por notícia para evitar travamentos.
    """
    detector = FraudDetector()
    input_path = Path(input_dir)
    
    if not input_path.exists():
        print(f"ERRO: Diretório {input_dir} não encontrado!")
        return
    
    json_files = sorted(list(input_path.glob("*.json")))
    total_files = len(json_files)
    
    # Verificar arquivos já processados
    already_processed = get_already_processed_files(output_file) if resume else set()
    
    # Carregar dados parciais se existirem
    fraud_news = []
    fraud_news_with_companies = []
    if resume and already_processed:
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            fraud_news = data.get('fraud_news', [])
            # Reconstruir lista de CSV
            for entry in fraud_news:
                analysis = entry.get('analysis', {})
                if analysis.get('companies_involved'):
                    fraud_news_with_companies.append({
                        'file': entry['file'],
                        'title': entry['title'],
                        'url': entry['url'],
                        'text': '',  # Será preenchido depois se necessário
                        'companies': '; '.join(analysis['companies_involved']),
                        'people': '; '.join(analysis.get('people_involved', [])),
                        'fraud_types': '; '.join(analysis.get('fraud_types', [])),
                        'confidence': analysis.get('confidence', ''),
                        'execution_time_seconds': analysis.get('execution_time_seconds', 0)
                    })
            print(f"\n📂 RETOMANDO PROCESSAMENTO")
            print(f"   Já processadas: {len(already_processed)} notícias")
            print(f"   Fraudes detectadas anteriormente: {len(fraud_news)}")
            print(f"   Com empresas: {len(fraud_news_with_companies)}")
        except:
            already_processed = set()
    
    print(f"\n{'='*70}")
    print(f"Iniciando processamento de {total_files} notícias...")
    print(f"💾 Salvamento automático a cada 25 notícias")
    print(f"⏱️  Timeout: {TIMEOUT_SECONDS}s por notícia")
    if START_FROM > 0:
        print(f"➡️  Começando da notícia {START_FROM} (pulando 1-{START_FROM-1})")
    if already_processed:
        print(f"🔄 Modo retomada: pulando {len(already_processed)} já processadas")
    print(f"{'='*70}\n")
    
    processed = len(already_processed)
    skipped = 0
    timeouts = 0
    consecutive_403_errors = 0  # Contador de erros 403 consecutivos
    SAVE_INTERVAL = 25
    
    for index, json_file in enumerate(json_files, start=1):
        # Usar índice na lista ordenada como "número da notícia"
        news_number = index
        
        # Pular se antes do START_FROM
        if START_FROM > 0 and news_number < START_FROM:
            skipped += 1
            continue
        
        # Pular se já processado
        if json_file.name in already_processed:
            skipped += 1
            continue
        
        processed += 1
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                news_data = json.load(f)
            
            title = news_data.get("title", "")
            text = news_data.get("text", "")
            url = news_data.get("url", "")
            
            print(f"[{news_number}/{total_files}] Processando: {json_file.name}...")
            
            try:
                result = detector.analyze_fraud(text, title, timeout=TIMEOUT_SECONDS)
                # Resetar contador de 403 em caso de sucesso
                consecutive_403_errors = 0
            except OllamaError403 as e403:
                consecutive_403_errors += 1
                print(f"⚠️  Erro 403 consecutivo #{consecutive_403_errors}/{MAX_CONSECUTIVE_403_ERRORS}")
                
                if consecutive_403_errors >= MAX_CONSECUTIVE_403_ERRORS:
                    print(f"\n{'='*70}")
                    print(f"🛑 INTERROMPENDO PROCESSAMENTO")
                    print(f"   Motivo: {MAX_CONSECUTIVE_403_ERRORS} erros 403 consecutivos do Ollama")
                    print(f"   Última notícia processada: {json_file.name}")
                    print(f"   Total processadas até agora: {processed}")
                    print(f"{'='*70}\n")
                    
                    # Salvar progresso antes de parar
                    output_path = Path(output_file)
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump({
                            "total_processed": processed,
                            "total_fraud_related": len(fraud_news),
                            "total_with_companies": len(fraud_news_with_companies),
                            "stopped_reason": f"Múltiplos erros 403 consecutivos ({MAX_CONSECUTIVE_403_ERRORS})",
                            "last_file": json_file.name,
                            "fraud_news": fraud_news
                        }, f, ensure_ascii=False, indent=2)
                    save_csv_incremental(csv_file, fraud_news_with_companies)
                    print("💾 Progresso salvo antes de parar.")
                    return  # Parar processamento
                
                # Continuar para próxima notícia após erro 403
                continue
            
            # Contar timeouts
            if result.get('execution_time_seconds', 0) >= TIMEOUT_SECONDS - 1:
                timeouts += 1
            
            if result["is_fraud_related"]:
                fraud_entry = {
                    "file": json_file.name,
                    "title": title,
                    "url": url,
                    "analysis": result
                }
                fraud_news.append(fraud_entry)
                
                print(f"  ✓ FRAUDE DETECTADA (confiança: {result['confidence']}) - Tempo: {result.get('execution_time_seconds', 0)}s")
                print(f"    Tipos: {', '.join(result['fraud_types'])}")
                if result['companies_involved']:
                    print(f"    Empresas: {', '.join(result['companies_involved'])}")
                if result['people_involved']:
                    print(f"    Pessoas: {', '.join(result['people_involved'])}")
                
                if result['companies_involved']:
                    fraud_news_with_companies.append({
                        "file": json_file.name,
                        "title": title,
                        "url": url,
                        "text": text,
                        "companies": '; '.join(result['companies_involved']),
                        "people": '; '.join(result['people_involved']) if result['people_involved'] else '',
                        "fraud_types": '; '.join(result['fraud_types']),
                        "confidence": result['confidence'],
                        "execution_time_seconds": result.get('execution_time_seconds', 0)
                    })
                    if result['people_involved']:
                        print(f"    💰 BÔNUS: Pessoas também identificadas!")
                else:
                    if result['people_involved']:
                        print(f"    ⚠ Apenas pessoas identificadas (sem empresas) - não será incluída no CSV")
                    else:
                        print(f"    ⚠ Sem empresas identificadas - não será incluída no CSV")
            else:
                print(f"  ✗ Não relacionada a fraude empresarial")
        
        except Exception as e:
            print(f"  ✗ ERRO ao processar {json_file.name}: {e}")
            continue
        
        # Salvamento incremental a cada 25 notícias
        if processed % SAVE_INTERVAL == 0:
            print(f"\n{'='*70}")
            print(f"💾 SALVAMENTO AUTOMÁTICO - {processed}/{total_files} notícias processadas")
            print(f"{'='*70}")
            
            # Salvar JSON parcial
            output_path = Path(output_file)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "total_processed": processed,
                    "total_fraud_related": len(fraud_news),
                    "total_with_companies": len(fraud_news_with_companies),
                    "fraud_news": fraud_news
                }, f, ensure_ascii=False, indent=2)
            
            # Salvar CSV parcial
            save_csv_incremental(csv_file, fraud_news_with_companies)
            
            print(f"✓ JSON salvo: {len(fraud_news)} fraudes detectadas")
            print(f"✓ CSV salvo: {len(fraud_news_with_companies)} notícias com empresas")
            print(f"{'='*70}\n")
        
        print()
    
    all_execution_times = [entry['analysis'].get('execution_time_seconds', 0) for entry in fraud_news]
    total_execution_time = sum(all_execution_times)
    avg_execution_time = total_execution_time / len(all_execution_times) if all_execution_times else 0
    min_execution_time = min(all_execution_times) if all_execution_times else 0
    max_execution_time = max(all_execution_times) if all_execution_times else 0
    
    sorted_times = sorted(all_execution_times)
    median_execution_time = sorted_times[len(sorted_times)//2] if sorted_times else 0
    
    print(f"\n{'='*70}")
    print(f"PROCESSAMENTO CONCLUÍDO")
    print(f"{'='*70}")
    print(f"Total de notícias processadas: {processed}")
    if skipped > 0:
        print(f"Notícias puladas (já processadas): {skipped}")
    if timeouts > 0:
        print(f"⏱️  Notícias com timeout: {timeouts}")
    print(f"Notícias relacionadas a fraudes: {len(fraud_news)}")
    print(f"Notícias com empresas/pessoas identificadas: {len(fraud_news_with_companies)}")
    print(f"\nMétricas de Performance:")
    print(f"  Tempo total: {total_execution_time:.2f}s ({total_execution_time/60:.2f} min)")
    print(f"  Tempo médio por notícia: {avg_execution_time:.2f}s")
    print(f"  Tempo mínimo: {min_execution_time:.2f}s")
    print(f"  Tempo máximo: {max_execution_time:.2f}s")
    print(f"  Tempo mediano: {median_execution_time:.2f}s")
    print(f"{'='*70}\n")
    
    output_path = Path(output_file)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "total_processed": processed,
            "total_fraud_related": len(fraud_news),
            "total_with_companies": len(fraud_news_with_companies),
            "fraud_news": fraud_news
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Resultados JSON salvos em: {output_file}")
    
    metrics_data = {
        "model": SELECTED_MODEL,
        "ollama_host": OLLAMA_HOST,
        "temperature": LLM_TEMPERATURE,
        "timestamp": datetime.now().isoformat(),
        "processing_summary": {
            "total_news_processed": processed,
            "total_fraud_detected": len(fraud_news),
            "total_with_companies_or_people": len(fraud_news_with_companies),
            "fraud_detection_rate": round(len(fraud_news) / processed * 100, 2) if processed > 0 else 0,
            "companies_people_identification_rate": round(len(fraud_news_with_companies) / len(fraud_news) * 100, 2) if fraud_news else 0
        },
        "execution_metrics": {
            "total_time_seconds": round(total_execution_time, 2),
            "total_time_minutes": round(total_execution_time / 60, 2),
            "average_time_per_news": round(avg_execution_time, 2),
            "min_time_seconds": round(min_execution_time, 2),
            "max_time_seconds": round(max_execution_time, 2),
            "median_time_seconds": round(median_execution_time, 2)
        },
        "confidence_distribution": {
            "alta": sum(1 for entry in fraud_news if entry['analysis'].get('confidence') == 'alta'),
            "média": sum(1 for entry in fraud_news if entry['analysis'].get('confidence') == 'média'),
            "baixa": sum(1 for entry in fraud_news if entry['analysis'].get('confidence') == 'baixa')
        }
    }
    
    metrics_path = Path(metrics_file)
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics_data, f, ensure_ascii=False, indent=2)
    
    print(f"Métricas de performance salvas em: {metrics_file}")
    
    csv_path = Path(csv_file)
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        if fraud_news_with_companies:
            fieldnames = ['file', 'title', 'url', 'companies', 'people', 'fraud_types', 'confidence', 'summary', 'execution_time_seconds']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(fraud_news_with_companies)
            print(f"CSV com notícias de fraude empresarial salvo em: {csv_file}")
        else:
            print(f"⚠ Nenhuma notícia com empresas ou pessoas identificadas - CSV não criado")
    
    print(f"\n{'='*70}")
    print("RESUMO DAS FRAUDES COM EMPRESAS/PESSOAS IDENTIFICADAS:")
    print(f"{'='*70}\n")
    
    total_time = sum(entry.get('execution_time_seconds', 0) for entry in fraud_news_with_companies)
    avg_time = total_time / len(fraud_news_with_companies) if fraud_news_with_companies else 0
    
    print(f"Tempo total de processamento: {total_time:.2f}s")
    print(f"Tempo médio por notícia: {avg_time:.2f}s")
    print(f"{'='*70}\n")
    
    for i, entry in enumerate(fraud_news_with_companies, 1):
        print(f"{i}. {entry['file']} (Tempo: {entry.get('execution_time_seconds', 0)}s)")
        print(f"   Título: {entry['title'][:80]}...")
        if entry.get('companies'):
            print(f"   Empresas: {entry['companies']}")
        if entry.get('people'):
            print(f"   Pessoas: {entry['people']}")
        print(f"   Tipos de Fraude: {entry['fraud_types']}")
        print(f"   Confiança: {entry['confidence']}")
        print()


if __name__ == "__main__":
    INPUT_DIR = "/home/paulo/projects/main-server/collector/noticias/downloaded_news/nsc_consolidado"
    OUTPUT_JSON = "/home/paulo/projects/main-server/.PAULO/fraud_detection_nsc_consolidado_results.json"
    OUTPUT_CSV = "/home/paulo/projects/main-server/.PAULO/fraud_news_nsc_consolidado_with_companies.csv"
    OUTPUT_METRICS = "/home/paulo/projects/main-server/.PAULO/performance_metrics_nsc_consolidado.json"
    
    print("\n" + "="*70)
    print("DETECTOR DE FRAUDES EMPRESARIAIS EM NOTÍCIAS")
    print("="*70)
    print(f"Diretório de entrada: {INPUT_DIR}")
    print(f"Arquivo JSON de saída: {OUTPUT_JSON}")
    print(f"Arquivo CSV de saída: {OUTPUT_CSV}")
    print(f"Arquivo de métricas: {OUTPUT_METRICS}")
    print(f"Modelo: {SELECTED_MODEL}")
    print("="*70 + "\n")
    
    process_all_news(INPUT_DIR, OUTPUT_JSON, OUTPUT_CSV, OUTPUT_METRICS)
