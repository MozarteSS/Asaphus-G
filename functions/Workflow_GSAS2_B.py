import os
import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Adiciona o caminho do GSAS-II ao sys.path automaticamente
_gsas2_path = Path(__file__).parent.parent / ".venv_gsas2" / "GSAS-II"
_gsas2_path = os.path.abspath(_gsas2_path)
if _gsas2_path not in sys.path:
    sys.path.insert(0, _gsas2_path)

try:
    from GSASII import GSASIIscriptable as G2sc
except ImportError:
    logger.error("GSASIIscriptable não encontrado. Caminho verificado: %s", _gsas2_path)
    sys.exit(1)


def executar_refinamento_com_config(config: dict):
    # Extração facilitada das variáveis do dicionário
    p = config["projeto"]
    w = config["workflow"]
    t = config["ajustes_tecnicos"]
    
    logger.info(f"--- Iniciando Projeto: {p['nome']} ---")
    
    # Setup de caminhos
    base_dir = Path("./projects/results") / p['nome']
    base_dir.mkdir(parents=True, exist_ok=True)
    gpx = G2sc.G2Project(newgpx=str(base_dir / f"{p['nome']}.gpx"))

    # Adiciona histograma e fases
    hist = gpx.add_powder_histogram(p['drx_path'], p['inst_path'])
    for cif in p['cif_paths']:
        gpx.add_phase(cif, phasename=Path(cif).stem, histograms=[hist])

    # --- Execução Condicional do Workflow ---
    
    # Passo 1: Background e Escala
    if w['refinar_background'] or w['refinar_escala']:
        gpx.do_refinements([{"set": {
            "Background": w['refinar_background'], 
            "Scale": w['refinar_escala']
        }, "cycles": t['max_cycles']}])

    # Passo 2: Deslocamento
    if w['refinar_deslocamento']:
        gpx.do_refinements([{"set": {"Sample Parameters": ["DisplaceX"]}, "cycles": t['max_cycles']}])

    # Passo 3: Rede
    if w['refinar_rede']:
        gpx.do_refinements([{"set": {"Cell": True}, "cycles": t['max_cycles']}])

    # Passo 4: Perfil
    if w['refinar_perfil']:
        gpx.do_refinements([{"set": {
            "Size": {"type": t['size_model'], "refine": True},
            "Mustrain": {"type": t['mustrain_model'], "refine": True},
        }, "cycles": t['max_cycles']}])

    # Passo 5: Átomos (Seguindo a lista de etapas definida no dicionário)
    if w['refinar_atomos']['ativar']:
        for etapa in w['refinar_atomos']['etapas']:
            logger.info(f"Refinando átomos: Etapa {etapa}")
            gpx.do_refinements([{"set": {"Atoms": {"all": etapa}}, "cycles": t['max_cycles']}])

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
    logger.info("Projeto salvo em: %s/", base_dir)

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
