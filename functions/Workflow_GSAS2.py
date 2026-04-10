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
    Aceita uma ou mais fases (arquivo_cif pode ser uma string ou lista de strings).
    Calcula o percentual de cada fase ao final.
    """
    print(f"--- Iniciando Projeto: {nome_projeto} ---")

    # 1. Cria o projeto do GSAS-II (.gpx) já no diretório de resultados
    results_dir = f"./projects/{nome_projeto}/results"
    os.makedirs(results_dir, exist_ok=True)
    gpx = G2sc.G2Project(newgpx=f"{results_dir}/{nome_projeto}")

    # 2. Carrega os Dados (Espectro DRX e Parâmetros do Difratômetro)
    hist = gpx.add_powder_histogram(arquivo_drx, arquivo_inst)

    # 3. Carrega as Fases Estruturais
    if isinstance(arquivo_cif, str):
        arquivos_cif = [arquivo_cif]
    else:
        arquivos_cif = arquivo_cif
    fases = []
    for cif in arquivos_cif:
        nome_fase = os.path.splitext(os.path.basename(cif))[0]
        fase = gpx.add_phase(cif, phasename=nome_fase, histograms=[hist])
        fases.append(fase)

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
    gpx.save()

    # 5. Extração e Relatório dos Resultados Estatísticos
    resultados = hist.residuals
    fator_rwp = resultados.get('wR', 'N/A')
    fator_rwpb = resultados.get('wRb', 'N/A')

    print("\n--- Resultados Finais ---")
    print(f"Fator wR (Desejável < 10%): {fator_rwp}%")
    print(f"Fator wRb: {fator_rwpb}%")
    print(f"Projeto salvo com sucesso em: {results_dir}/")

    # 6. Calcula e exibe o percentual de cada fase
    try:
        wt_fracs = gpx.get_wt_fractions(hist)
        print("\nPercentual de cada fase na amostra:")
        for fase_nome, wt in wt_fracs.items():
            print(f"- {fase_nome}: {wt:.2f}%")
    except Exception as e:
        print("Não foi possível calcular o percentual das fases:", e)

    # 7. Retorna dados para plotagem e percentuais
    return {
        "x": hist.getdata("X"),
        "yobs": hist.getdata("Yobs"),
        "ycalc": hist.getdata("Ycalc"),
        "ybkg": hist.getdata("Background"),
        "diff": hist.getdata("Residual"),
        "wR": fator_rwp,
        "wRb": fator_rwpb,
        "percentuais_fases": wt_fracs if 'wt_fracs' in locals() else None,
    }

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