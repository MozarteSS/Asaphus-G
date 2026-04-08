import os
import sys

# OBS: Ative o ambiente e use PYTHONPATH antes de rodar:
#   source gsas2_env/bin/activate
#   PYTHONPATH="./gsas2_env/GSAS-II" python Workflow_GSAS-II.py
try:
    from GSASII import GSASIIscriptable as G2sc
except ImportError:
    print("Erro: GSASIIscriptable não encontrado.")
    print("Execute com: PYTHONPATH=\"./gsas2_env/GSAS-II\" python Workflow_GSAS-II.py")
    sys.exit()

def refinamento_sequencial_oxidos(arquivo_drx, arquivo_inst, arquivo_cif, nome_projeto):
    """
    Executa o workflow seguro de refinamento de Rietveld passo a passo.
    """
    print(f"--- Iniciando Projeto: {nome_projeto} ---")
    
    # 1. Cria o projeto do GSAS-II (.gpx)
    gpx = G2sc.G2Project(newgpx=nome_projeto)
    
    # 2. Carrega os Dados (Espectro DRX e Parâmetros do Difratômetro)
    # arquivo_inst contém as configs do seu aparelho (ex: tubo de Cu, fendas, etc)
    hist = gpx.add_histogram(arquivo_drx, arquivo_inst)
    
    # 3. Carrega a Fase Estrutural (ex: Hematita ou Magnetita)
    fase = gpx.add_phase(arquivo_cif, phasename="Fase_Principal", histograms=[hist])
    
    # --- INÍCIO DO WORKFLOW DE REFINAMENTO ---
    
    # PASSO 1: Escala e Background
    # Alinha a altura geral do gráfico e ajusta o ruído de fundo (polinômio)
    print("Passo 1: Refinando Escala e Background...")
    gpx.do_refinements([{"set": {"Background": True, "PhaseFractions": True}}])
    
    # PASSO 2: Deslocamento da Amostra (Zero-shift)
    # Alinha a posição horizontal dos picos (corrige altura da amostra no porta-amostras)
    print("Passo 2: Refinando Deslocamento da Amostra (Sample Displacement)...")
    gpx.do_refinements([{"set": {"SamplePos": True}}])
    
    # PASSO 3: Parâmetros de Rede (Célula Unitária)
    # Ajusta o tamanho da célula a, b, c. Essencial para acomodar substituições iônicas.
    print("Passo 3: Refinando Parâmetros de Rede (Cell)...")
    gpx.do_refinements([{"set": {"Cell": True}}])
    
    # PASSO 4: Perfil de Pico (Tamanho de Cristalito e Microdeformação)
    # Ajusta o alargamento dos picos. Crucial para nanomateriais.
    print("Passo 4: Refinando Perfil (Tamanho e Microstrain)...")
    gpx.do_refinements([{"set": {"Size": True, "Microstrain": True}}])
    
    # PASSO 5: Parâmetros Estruturais (Coordenadas Atômicas)
    # O passo mais sensível. Move os átomos dentro da célula.
    # Em óxidos de ferro rotineiros, às vezes este passo é omitido se a qualidade do DRX for baixa.
    print("Passo 5: Refinando Posições Atômicas...")
    gpx.do_refinements([{"set": {"Atoms": True}}])
    
    # --- FIM DO WORKFLOW ---
    
    # 4. Salva o projeto final
    gpx.save(nome_projeto)
    
    # 5. Extração e Relatório dos Resultados Estatísticos
    resultados = hist.get_recent_refinement_results()
    fator_rwp = resultados.get('Rwp', 'N/A')
    fator_gof = resultados.get('GOF', 'N/A') # Goodness of fit (Chi-quadrado)
    
    print("\n--- Resultados Finais ---")
    print(f"Fator Rwp (Desejável < 10%): {fator_rwp}%")
    print(f"Chi-quadrado (Desejável próximo a 1): {fator_gof}")
    print(f"Projeto salvo com sucesso em: {nome_projeto}")

# ==========================================
# Exemplo de uso prático
# ==========================================
if __name__ == "__main__":
    # Arquivos fictícios para exemplificar o seu caso
    DRX_LAB = "amostra_oxido_01.txt"       # Seu dado exportado do difratômetro
    INST_PRM = "difratometro_lab.instprm"  # Arquivo de calibração do aparelho
    CIF_REF = "hematita_referencia.cif"    # Baixado do banco COD
    PROJETO = "analise_hematita.gpx"
    
    # Descomente a linha abaixo para executar se tiver os arquivos reais na mesma pasta
    # refinamento_sequencial_oxidos(DRX_LAB, INST_PRM, CIF_REF, PROJETO)