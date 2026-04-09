import os
import sys

# Adiciona o caminho do GSAS-II ao sys.path automaticamente
_gsas2_path = os.path.join(os.path.dirname(__file__), os.pardir, ".venv_gsas2", "GSAS-II")
_gsas2_path = os.path.abspath(_gsas2_path)
if _gsas2_path not in sys.path:
    sys.path.insert(0, _gsas2_path)

try:
    from GSASII import GSASIIscriptable as G2sc
except ImportError:
    print("Erro: GSASIIscriptable não encontrado.")
    print(f"Caminho verificado: {_gsas2_path}")
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
    hist = gpx.add_powder_histogram(arquivo_drx, arquivo_inst)
    
    # 3. Carrega a Fase Estrutural (ex: Hematita ou Magnetita)
    fase = gpx.add_phase(arquivo_cif, phasename="Fase_Principal", histograms=[hist])
    
    # --- INÍCIO DO WORKFLOW DE REFINAMENTO ---
    
    # PASSO 1: Escala e Background
    # Alinha a altura geral do gráfico e ajusta o ruído de fundo (polinômio)
    print("Passo 1: Refinando Escala e Background...")
    gpx.do_refinements([{"set": {"Background": True, "Scale": True}}])
    
    # PASSO 2: Deslocamento da Amostra (Zero-shift)
    # Alinha a posição horizontal dos picos (corrige altura da amostra no porta-amostras)
    print("Passo 2: Refinando Deslocamento da Amostra (Sample Displacement)...")
    gpx.do_refinements([{"set": {"Sample Parameters": ["DisplaceX", "DisplaceY"]}}])
    
    # PASSO 3: Parâmetros de Rede (Célula Unitária)
    # Ajusta o tamanho da célula a, b, c. Essencial para acomodar substituições iônicas.
    print("Passo 3: Refinando Parâmetros de Rede (Cell)...")
    gpx.do_refinements([{"set": {"Cell": True}}])
    
    # PASSO 4: Perfil de Pico (Tamanho de Cristalito e Microdeformação)
    # Ajusta o alargamento dos picos. Crucial para nanomateriais.
    print("Passo 4: Refinando Perfil (Tamanho e Microstrain)...")
    gpx.do_refinements([{"set": {
        "Size": {"type": "isotropic", "refine": True},
        "Mustrain": {"type": "isotropic", "refine": True}
    }}])
    
    # PASSO 5: Parâmetros Estruturais (Coordenadas Atômicas)
    # O passo mais sensível. Move os átomos dentro da célula.
    # Em óxidos de ferro rotineiros, às vezes este passo é omitido se a qualidade do DRX for baixa.
    print("Passo 5: Refinando Posições Atômicas...")
    gpx.do_refinements([{"set": {"Atoms": {"all": "XU"}}}])
    
    # --- FIM DO WORKFLOW ---
    
    # 4. Salva o projeto final
    gpx.save(nome_projeto)
    
    # 5. Extração e Relatório dos Resultados Estatísticos
    resultados = hist.residuals
    fator_rwp = resultados.get('wR', 'N/A')
    fator_rwpb = resultados.get('wRb', 'N/A')

    print("\n--- Resultados Finais ---")
    print(f"Fator wR (Desejável < 10%): {fator_rwp}%")
    print(f"Fator wRb: {fator_rwpb}%")
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