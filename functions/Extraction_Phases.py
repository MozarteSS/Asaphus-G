import re

def extrair_fracoes_fase(caminho_arquivo):
    resultados = {}
    fase_atual = None
    
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            for linha in arquivo:
                # 1. Identifica o bloco final de cada fase buscando por "Phase: [Nome] in histogram"
                match_fase = re.search(r'Phase:\s*(.+?)\s*in histogram:', linha)
                if match_fase:
                    fase_atual = match_fase.group(1).strip()
                
                # 2. Busca a linha que contém os resultados finais das frações
                if "Phase fraction" in linha and "Weight fraction" in linha and fase_atual:
                    # Captura os números (incluindo notação científica como 1e-12)
                    match_pf = re.search(r'Phase fraction\s*:\s*([0-9\.eE+-]+)', linha)
                    match_wf = re.search(r'Weight fraction\s*:\s*([0-9\.eE+-]+)', linha)
                    
                    # Salva os dados no dicionário
                    resultados[fase_atual] = {
                        'Phase Fraction': float(match_pf.group(1)) if match_pf else None,
                        'Weight Fraction': float(match_wf.group(1)) if match_wf else None
                    }
                    
                    # Reseta a fase atual para evitar sobrescritas acidentais
                    fase_atual = None
                    
    except FileNotFoundError:
        return "Erro: Arquivo não encontrado. Verifique o caminho especificado."
    except Exception as e:
        return f"Ocorreu um erro: {e}"
        
    return resultados