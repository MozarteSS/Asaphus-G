import re
import logging

logger = logging.getLogger(__name__)


def extrair_fracoes_fase(caminho_arquivo: str) -> dict[str, dict[str, float | None]] | str:
    """
    Extrai frações de fase e de peso do arquivo .lst gerado pelo GSAS-II.

    Args:
        caminho_arquivo: Caminho para o arquivo .lst do refinamento.

    Returns:
        Dicionário no formato::

            {
                "NomeFase": {
                    "Phase Fraction": float,
                    "Weight Fraction": float,
                }
            }

        Retorna uma string de erro se o arquivo não for encontrado ou ocorrer
        algum problema de leitura.
    """
    resultados: dict[str, dict[str, float | None]] = {}
    fase_atual: str | None = None

    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
            for linha in arquivo:
                # Identifica o bloco final de cada fase buscando "Phase: [Nome] in histogram"
                match_fase = re.search(r'Phase:\s*(.+?)\s*in histogram:', linha)
                if match_fase:
                    fase_atual = match_fase.group(1).strip()

                # Busca a linha que contém os resultados finais das frações
                if "Phase fraction" in linha and "Weight fraction" in linha and fase_atual:
                    match_pf = re.search(r'Phase fraction\s*:\s*([0-9\.eE+-]+)', linha)
                    match_wf = re.search(r'Weight fraction\s*:\s*([0-9\.eE+-]+)', linha)

                    pf = float(match_pf.group(1)) if match_pf else None
                    wf = float(match_wf.group(1)) if match_wf else None

                    resultados[fase_atual] = {
                        'Phase Fraction': pf,
                        'Weight Fraction': wf,
                    }
                    fase_atual = None

    except FileNotFoundError:
        return f"Erro: arquivo não encontrado — '{caminho_arquivo}'"
    except Exception as e:
        return f"Erro ao ler o arquivo: {e}"

    # Valida se as frações de peso somam aproximadamente 1 (tolerância de 5%)
    wf_values = [v['Weight Fraction'] for v in resultados.values() if v['Weight Fraction'] is not None]
    if wf_values:
        total_wf = sum(wf_values)
        if not (0.95 <= total_wf <= 1.05):
            logger.warning(
                "Soma das frações de peso = %.4f (esperado ≈ 1.0). "
                "Verifique se o refinamento convergiu corretamente.",
                total_wf,
            )

    return resultados
