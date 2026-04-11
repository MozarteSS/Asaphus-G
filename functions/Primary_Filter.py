import os
import logging
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from scipy.spatial.distance import cosine
from pymatgen.core import Structure
from pymatgen.analysis.diffraction.xrd import XRDCalculator

logger = logging.getLogger(__name__)


def normalizar(arr: np.ndarray) -> np.ndarray:
    """Normaliza um array para o intervalo [0, 1]. Retorna zeros se range == 0."""
    rng = arr.max() - arr.min()
    if rng == 0:
        return np.zeros_like(arr, dtype=float)
    return (arr - arr.min()) / rng


def listar_cif_para_dict(caminho_pasta: str) -> dict[str, str]:
    """
    Lista todos os arquivos .cif em uma pasta e retorna um dicionário
    com os nomes dos arquivos como chaves e os caminhos completos como valores.

    Args:
        caminho_pasta: Caminho da pasta a ser pesquisada.

    Returns:
        Dicionário {nome_do_arquivo: caminho_completo}. Vazio se a pasta não existir.
    """
    if not os.path.isdir(caminho_pasta):
        logger.error("Caminho '%s' não é uma pasta válida.", caminho_pasta)
        return {}
    logger.info("Buscando CIFs em: %s", caminho_pasta)
    dicionario_paths = {}
    for arquivo in os.listdir(caminho_pasta):
        if arquivo.endswith(".cif"):
            caminho_completo = os.path.join(caminho_pasta, arquivo)
            if os.path.isfile(caminho_completo):
                dicionario_paths[arquivo] = caminho_completo
    return dicionario_paths


def carregar_amostra(input_file: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Carrega o arquivo TXT de difração (formato RRUFF: cabeçalho ## e dados 2θ, intensidade).

    Returns:
        (theta, intensidade) como arrays numpy.

    Raises:
        ValueError: se o arquivo não contiver nenhuma linha de dados válida.
    """
    theta = []
    intensidade = []
    with open(input_file, 'r') as f:
        for linha in f:
            linha = linha.strip()
            if not linha or linha.startswith('##'):
                continue
            partes = linha.split(',')
            if len(partes) == 2:
                try:
                    theta.append(float(partes[0]))
                    intensidade.append(float(partes[1]))
                except ValueError:
                    continue
    if not theta:
        raise ValueError(f"Nenhum dado de difração encontrado em '{input_file}'.")
    return np.array(theta), np.array(intensidade)


def simular_padrao_xrd(
    arquivo_cif: str,
    two_theta_grid: np.ndarray,
    sigma: float = 0.1,
) -> np.ndarray:
    """
    Simula um padrão XRD contínuo a partir de um CIF, projetado no grid de 2θ da amostra.

    Args:
        arquivo_cif:    Caminho para o arquivo .cif.
        two_theta_grid: Array de valores 2θ da amostra experimental.
        sigma:          Largura do alargamento Gaussiano em graus (padrão: 0.1°).
                        Valor típico para instrumentos de laboratório com resolução ~0.02–0.05°.

    Returns:
        Array de intensidades simuladas no mesmo grid de 2θ da amostra.
    """
    estrutura = Structure.from_file(arquivo_cif)
    calc = XRDCalculator(wavelength="CuKa")
    padrao = calc.get_pattern(estrutura, two_theta_range=(two_theta_grid.min(), two_theta_grid.max()))

    intensidade_sim = np.zeros_like(two_theta_grid)
    for pos, intens in zip(padrao.x, padrao.y):
        intensidade_sim += intens * np.exp(-0.5 * ((two_theta_grid - pos) / sigma) ** 2)

    return intensidade_sim


def primary_filter(
    correlation: str = "pearson",
    input_file: str | None = None,
    ref_dir: str | None = None,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Filtra as fases candidatas comparando a amostra experimental com padrões simulados.

    Args:
        correlation: Método de correlação — "pearson" (padrão) ou "cosine".
        input_file:  Caminho para o arquivo .txt da amostra (obrigatório).
        ref_dir:     Caminho para o diretório com os CIFs de referência (obrigatório).

    Returns:
        (df, amostra_norm, theta): DataFrame ordenado por score (decrescente),
        array de intensidade normalizada da amostra e array de ângulos 2θ.
    """
    if input_file is None or ref_dir is None:
        raise ValueError("'input_file' e 'ref_dir' são obrigatórios.")

    # 1. Carrega a amostra real (TXT com 2θ, intensidade)
    theta_amostra, int_amostra = carregar_amostra(input_file)
    amostra_int_norm = normalizar(int_amostra)

    # 2. Dicionário com as referências candidatas (CIFs)
    candidatos = listar_cif_para_dict(str(ref_dir))

    # 3. Simula XRD de cada CIF e compara com a amostra
    resultados = []
    for nome, arquivo_cif in candidatos.items():
        try:
            int_sim = simular_padrao_xrd(arquivo_cif, theta_amostra)
            ref_int_norm = normalizar(int_sim)
            if correlation == "pearson":
                score, _ = pearsonr(amostra_int_norm, ref_int_norm)
            elif correlation == "cosine":
                score = 1 - cosine(amostra_int_norm, ref_int_norm)
            else:
                logger.warning("Correlação '%s' não reconhecida. Usando Pearson.", correlation)
                score, _ = pearsonr(amostra_int_norm, ref_int_norm)
            resultados.append({"nome": nome, "score": score, "ref_int_norm": ref_int_norm})
        except Exception as e:
            logger.warning("Não foi possível processar %s: %s", nome, e)

    # 4. Retorna DataFrame ordenado (do melhor para o pior)
    df = pd.DataFrame(resultados).sort_values(by="score", ascending=False).reset_index(drop=True)
    return df, amostra_int_norm, theta_amostra
