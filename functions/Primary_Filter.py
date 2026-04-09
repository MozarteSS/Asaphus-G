import os
import numpy as np
from scipy.stats import pearsonr
from pymatgen.core import Structure
from pymatgen.analysis.diffraction.xrd import XRDCalculator

def listar_cif_para_dict(caminho_pasta):
    """
    Lista todos os arquivos .cif em uma pasta e retorna um dicionário
    com os nomes dos arquivos como chaves e os caminhos completos como valores.

    Parâmetros:
    caminho_pasta (str): Caminho da pasta a ser pesquisada.

    Retorna:
    dict: Dicionário {nome_do_arquivo: caminho_completo} para cada arquivo .cif.
          Retorna um dicionário vazio se a pasta não existir ou não houver .cif.
    """
    if not os.path.isdir(caminho_pasta):
        print(f"Erro: O caminho '{caminho_pasta}' não é uma pasta válida.")
        return {}
    print(caminho_pasta)
    dicionario_paths = {}

    for arquivo in os.listdir(caminho_pasta):
        if arquivo.endswith(".cif"):
            caminho_completo = os.path.join(caminho_pasta, arquivo)
            if os.path.isfile(caminho_completo):
                dicionario_paths[arquivo] = caminho_completo

    return dicionario_paths


def carregar_amostra(input_file):
    """
    Carrega o arquivo TXT de difração (formato RRUFF: cabeçalho ## e dados 2θ, intensidade).
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
                theta.append(float(partes[0]))
                intensidade.append(float(partes[1]))
    return np.array(theta), np.array(intensidade)


def simular_padrao_xrd(arquivo_cif, two_theta_grid, sigma=0.1):
    """
    Simula um padrão XRD contínuo a partir de um CIF, projetado no grid de 2θ da amostra.
    Usa pymatgen para calcular posições e intensidades dos picos,
    e alarga cada pico com uma Gaussiana.
    """
    estrutura = Structure.from_file(arquivo_cif)
    calc = XRDCalculator(wavelength="CuKa")
    padrao = calc.get_pattern(estrutura, two_theta_range=(two_theta_grid.min(), two_theta_grid.max()))

    intensidade_sim = np.zeros_like(two_theta_grid)
    for pos, intens in zip(padrao.x, padrao.y):
        intensidade_sim += intens * np.exp(-0.5 * ((two_theta_grid - pos) / sigma) ** 2)

    return intensidade_sim


def primary_filter(input_file="minha_amostra_bancada.txt", ref_dir="ref/"):

    # 1. Carrega a amostra real (TXT com 2θ, intensidade)
    theta_amostra, int_amostra = carregar_amostra(input_file)
    amostra_int_norm = (int_amostra - int_amostra.min()) / int_amostra.max()

    # 2. Dicionário com as referências candidatas (CIFs)
    candidatos = listar_cif_para_dict(ref_dir)

    # 3. Simula XRD de cada CIF e compara com a amostra
    ranking = {}
    for nome, arquivo_cif in candidatos.items():
        try:
            int_sim = simular_padrao_xrd(arquivo_cif, theta_amostra)
            ref_int_norm = (int_sim - int_sim.min()) / (int_sim.max() or 1.0)

            score, _ = pearsonr(amostra_int_norm, ref_int_norm)
            ranking[nome] = score
        except Exception as e:
            print(f"Aviso: Não foi possível processar {nome}: {e}")

    # 4. Exibe os resultados ordenados (do melhor para o pior)
    print("--- RANKING DE FASES (Score de Similaridade) ---")
    for nome, score in sorted(ranking.items(), key=lambda x: x[1], reverse=True):
        print(f"{nome}: {score:.2%}")