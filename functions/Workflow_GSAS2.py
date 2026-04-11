import os
import sys
import logging

logger = logging.getLogger(__name__)

# Adiciona o caminho do GSAS-II ao sys.path automaticamente
_gsas2_path = os.path.join(os.path.dirname(__file__), os.pardir, ".venv_gsas2", "GSAS-II")
_gsas2_path = os.path.abspath(_gsas2_path)
if _gsas2_path not in sys.path:
    sys.path.insert(0, _gsas2_path)

try:
    from GSASII import GSASIIscriptable as G2sc
except ImportError:
    logger.error("GSASIIscriptable não encontrado. Caminho verificado: %s", _gsas2_path)
    sys.exit(1)


def refinamento_sequencial_oxidos(
    arquivo_drx: str,
    arquivo_inst: str,
    arquivo_cif: str | list[str],
    nome_projeto: str,
    refinar_atomos: bool = True,
) -> dict:
    """
    Executa o workflow de refinamento de Rietveld passo a passo via GSAS-II.

    Aceita uma ou mais fases (arquivo_cif pode ser string ou lista de strings).
    Calcula o percentual de cada fase ao final.

    Args:
        arquivo_drx:    Caminho para o arquivo de dados XRD (.txt, formato RRUFF).
        arquivo_inst:   Caminho para o arquivo de parâmetros do difratômetro (.prm).
        arquivo_cif:    Caminho(s) para o(s) arquivo(s) CIF das fases a refinar.
        nome_projeto:   Nome do projeto (usado para nomear arquivos de saída).
        refinar_atomos: Se True (padrão), executa o Passo 5 de refinamento de posições
                        atômicas. Desative para dados de baixa qualidade onde este passo
                        pode divergir.

    Returns:
        Dicionário com dados de plotagem (x, yobs, ycalc, ybkg, diff),
        fatores de qualidade (wR, wRb) e percentuais de fase.
    """
    logger.info("--- Iniciando Projeto: %s ---", nome_projeto)

    # 1. Cria o projeto do GSAS-II (.gpx) no diretório de resultados
    results_dir = f"./projects/{nome_projeto}/results"
    os.makedirs(results_dir, exist_ok=True)
    gpx = G2sc.G2Project(newgpx=f"{results_dir}/{nome_projeto}")

    # 2. Carrega os dados (espectro XRD e parâmetros do difratômetro)
    hist = gpx.add_powder_histogram(arquivo_drx, arquivo_inst)

    # 3. Carrega as fases estruturais
    arquivos_cif = [arquivo_cif] if isinstance(arquivo_cif, str) else arquivo_cif
    fases = []
    for cif in arquivos_cif:
        nome_fase = os.path.splitext(os.path.basename(cif))[0]
        fase = gpx.add_phase(cif, phasename=nome_fase, histograms=[hist])
        fases.append(fase)

    # --- INÍCIO DO WORKFLOW DE REFINAMENTO ---

    # Passo 1: Escala e Background
    # Alinha a altura geral do gráfico e ajusta o ruído de fundo (polinômio).
    logger.info("Passo 1: Refinando Escala e Background...")
    gpx.do_refinements([{"set": {"Background": True, "Scale": True}}])

    # Passo 2: Deslocamento da Amostra (Zero-shift)
    # Alinha a posição horizontal dos picos (corrige altura da amostra no porta-amostras).
    logger.info("Passo 2: Refinando Deslocamento da Amostra (Sample Displacement)...")
    gpx.do_refinements([{"set": {"Sample Parameters": ["DisplaceX", "DisplaceY"]}}])

    # Passo 3: Parâmetros de Rede (Célula Unitária)
    # Ajusta o tamanho da célula a, b, c. Essencial para acomodar substituições iônicas.
    logger.info("Passo 3: Refinando Parâmetros de Rede (Cell)...")
    gpx.do_refinements([{"set": {"Cell": True}}])

    # Passo 4: Perfil de Pico (Tamanho de Cristalito e Microdeformação)
    # Ajusta o alargamento dos picos. Crucial para nanomateriais.
    logger.info("Passo 4: Refinando Perfil (Tamanho e Microstrain)...")
    gpx.do_refinements([{"set": {
        "Size": {"type": "isotropic", "refine": True},
        "Mustrain": {"type": "isotropic", "refine": True},
    }}])

    # Passo 5: Parâmetros Estruturais (Coordenadas Atômicas)
    # O passo mais sensível — move os átomos dentro da célula.
    # Use refinar_atomos=False se a qualidade do XRD for baixa.
    if refinar_atomos:
        logger.info("Passo 5: Refinando Posições Atômicas...")
        gpx.do_refinements([{"set": {"Atoms": {"all": "XU"}}}])
    else:
        logger.info("Passo 5: Refinamento de posições atômicas pulado (refinar_atomos=False).")

    # --- FIM DO WORKFLOW ---

    # 4. Salva o projeto final
    gpx.save()

    # 5. Extração dos fatores de qualidade
    resultados = hist.residuals
    fator_rwp = resultados.get('wR', 'N/A')
    fator_rwpb = resultados.get('wRb', 'N/A')

    logger.info("--- Resultados Finais ---")
    logger.info("Fator wR (Desejável < 10%%): %s%%", fator_rwp)
    logger.info("Fator wRb: %s%%", fator_rwpb)
    logger.info("Projeto salvo em: %s/", results_dir)

    # 6. Calcula o percentual de cada fase
    wt_fracs = None
    try:
        wt_fracs = gpx.get_wt_fractions(hist)
        logger.info("Percentual de cada fase na amostra:")
        for fase_nome, wt in wt_fracs.items():
            logger.info("  %s: %.2f%%", fase_nome, wt)
    except Exception as e:
        logger.warning("Não foi possível calcular o percentual das fases: %s", e)

    # 7. Retorna dados para plotagem e percentuais
    return {
        "x": hist.getdata("X"),
        "yobs": hist.getdata("Yobs"),
        "ycalc": hist.getdata("Ycalc"),
        "ybkg": hist.getdata("Background"),
        "diff": hist.getdata("Residual"),
        "wR": fator_rwp,
        "wRb": fator_rwpb,
        "percentuais_fases": wt_fracs,
    }


# ==========================================
# Exemplo de uso prático
# ==========================================
if __name__ == "__main__":
    DRX_LAB = "amostra_oxido_01.txt"
    INST_PRM = "difratometro_lab.instprm"
    CIF_REF = "hematita_referencia.cif"
    PROJETO = "analise_hematita"

    # Descomente para executar com os arquivos reais:
    # refinamento_sequencial_oxidos(DRX_LAB, INST_PRM, CIF_REF, PROJETO)
