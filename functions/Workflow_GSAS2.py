import sys
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Adiciona o caminho do GSAS-II ao sys.path automaticamente
_gsas2_path = (Path(__file__).parent.parent / ".venv_gsas2" / "GSAS-II").resolve()
if str(_gsas2_path) not in sys.path:
    sys.path.insert(0, str(_gsas2_path))

try:
    from GSASII import GSASIIscriptable as G2sc
except ImportError as e:
    raise ImportError(
        f"GSASIIscriptable não encontrado. Caminho verificado: {_gsas2_path}"
    ) from e


def executar_refinamento_com_config(config: dict) -> dict:
    """
    Executa o workflow de refinamento de Rietveld via GSAS-II a partir de um dicionário
    de configuração.

    Args:
        config: Dicionário com três sub-dicionários obrigatórios:

            "projeto": {
                "nome":      str  — nome do projeto (usado para nomear arquivos de saída),
                "drx_path":  str  — caminho para o arquivo XRD (.txt, formato RRUFF),
                "inst_path": str  — caminho para o arquivo de parâmetros do difratômetro (.instprm),
                "cif_paths": list[str]  — lista de caminhos para os arquivos CIF das fases,
            }

            "workflow": {
                "refinar_background":  bool  — refina o fundo (polinômio),
                "refinar_escala":      bool  — refina a escala global,
                "refinar_deslocamento": bool  — refina o deslocamento da amostra (DisplaceX, DisplaceY),
                "refinar_rede":        bool  — refina os parâmetros de rede (célula unitária),
                "refinar_perfil":      bool  — refina o perfil de pico (tamanho e microstrain),
                "refinar_atomos": {
                    "ativar": bool        — ativa o refinamento de átomos,
                    "etapas": list[str]   — sequência de flags GSAS-II, ex: ["X", "XU"],
                },
            }

            "ajustes_tecnicos": {
                "max_cycles":      int  — número máximo de ciclos por etapa,
                "size_model":      str  — modelo de tamanho de cristalito, ex: "isotropic",
                "mustrain_model":  str  — modelo de microstrain, ex: "isotropic",
            }

    Returns:
        Dicionário com:
            x, yobs, ycalc, ybkg, diff — arrays de dados para plotagem,
            wR, wRb                    — fatores de qualidade do refinamento,
            percentuais_fases          — dict {nome_fase: %} ou None se não disponível.
    """
    p = config["projeto"]
    w = config["workflow"]
    t = config["ajustes_tecnicos"]

    logger.info("--- Iniciando Projeto: %s ---", p["nome"])

    # Setup de caminhos
    base_dir = Path("./projects") / p["nome"] / "results"
    base_dir.mkdir(parents=True, exist_ok=True)
    gpx = G2sc.G2Project(newgpx=str(base_dir / p["nome"]))

    # Adiciona histograma e fases
    hist = gpx.add_powder_histogram(p["drx_path"], p["inst_path"])
    for cif in p["cif_paths"]:
        gpx.add_phase(cif, phasename=Path(cif).stem, histograms=[hist])

    # --- Execução Condicional do Workflow ---

    # Passo 1: Background e Escala
    if w["refinar_background"] or w["refinar_escala"]:
        logger.info("Passo 1: Refinando Background e Escala...")
        gpx.do_refinements([{"set": {
            "Background": w["refinar_background"],
            "Scale": w["refinar_escala"],
        }, "cycles": t["max_cycles"]}])

    # Passo 2: Deslocamento da Amostra
    if w["refinar_deslocamento"]:
        logger.info("Passo 2: Refinando Deslocamento da Amostra...")
        gpx.do_refinements([{"set": {
            "Sample Parameters": ["DisplaceX", "DisplaceY"],
        }, "cycles": t["max_cycles"]}])

    # Passo 3: Parâmetros de Rede
    if w["refinar_rede"]:
        logger.info("Passo 3: Refinando Parâmetros de Rede...")
        gpx.do_refinements([{"set": {"Cell": True}, "cycles": t["max_cycles"]}])

    # Passo 4: Perfil de Pico
    if w["refinar_perfil"]:
        logger.info("Passo 4: Refinando Perfil (Tamanho e Microstrain)...")
        gpx.do_refinements([{"set": {
            "Size": {"type": t["size_model"], "refine": True},
            "Mustrain": {"type": t["mustrain_model"], "refine": True},
        }, "cycles": t["max_cycles"]}])

    # Passo 5: Átomos (sequência de etapas definida no dicionário)
    if w["refinar_atomos"]["ativar"]:
        for etapa in w["refinar_atomos"]["etapas"]:
            logger.info("Passo 5: Refinando átomos — etapa '%s'...", etapa)
            gpx.do_refinements([{"set": {"Atoms": {"all": etapa}}, "cycles": t["max_cycles"]}])

    # --- FIM DO WORKFLOW ---

    gpx.save()

    # Extração dos fatores de qualidade
    resultados = hist.residuals
    fator_rwp = resultados.get("wR", "N/A")
    fator_rwpb = resultados.get("wRb", "N/A")

    logger.info("--- Resultados Finais ---")
    logger.info("Fator wR (Desejável < 10%%): %s%%", fator_rwp)
    logger.info("Fator wRb: %s%%", fator_rwpb)
    logger.info("Projeto salvo em: %s/", base_dir)

    # Calcula o percentual de cada fase
    wt_fracs = None
    try:
        wt_fracs = hist.ComputeMassFracs()
        logger.info("Percentual de cada fase na amostra:")
        for fase_nome, (val, su) in wt_fracs.items():
            logger.info("  %s: %.2f%% ± %.2f%%", fase_nome, val * 100, su * 100)
    except Exception as e:
        logger.warning("Não foi possível calcular o percentual das fases: %s", e)

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
    config_exemplo = {
        "projeto": {
            "nome": "analise_hematita",
            "drx_path": "amostra_oxido_01.txt",
            "inst_path": "difratometro_lab.instprm",
            "cif_paths": ["hematita_referencia.cif"],
        },
        "workflow": {
            "refinar_background": True,
            "refinar_escala": True,
            "refinar_deslocamento": True,
            "refinar_rede": True,
            "refinar_perfil": True,
            "refinar_atomos": {
                "ativar": True,
                "etapas": ["X", "XU"],
            },
        },
        "ajustes_tecnicos": {
            "max_cycles": 10,
            "size_model": "isotropic",
            "mustrain_model": "isotropic",
        },
    }

    # Descomente para executar com os arquivos reais:
    # resultado = executar_refinamento_com_config(config_exemplo)
