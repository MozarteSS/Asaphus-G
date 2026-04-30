import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from functions.Primary_Filter import normalizar, simular_padrao_xrd

logger = logging.getLogger(__name__)


def plot_filtro_primario(
    theta: np.ndarray,
    amostra_norm: np.ndarray,
    df: pd.DataFrame,
    top_n: int = 1,
) -> None:
    """
    Plota a amostra experimental contra as melhores referências do filtro primário.

    Args:
        theta:       Array de ângulos 2θ da amostra.
        amostra_norm: Intensidade normalizada da amostra experimental.
        df:          DataFrame retornado por primary_filter(), ordenado por score.
        top_n:       Número de melhores referências a plotar (padrão: 1).
    """
    for _, row in df.head(top_n).iterrows():
        nome = row['nome']
        score = row['score']
        ref_int_norm = row['ref_int_norm']

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(theta, amostra_norm, label="Amostra (experimental)", linewidth=0.8)
        ax.plot(
            theta, ref_int_norm,
            label=f"Referência: {nome} (score={score:.2%})",
            linewidth=0.8, alpha=0.8,
        )
        ax.set_xlabel("2θ (°)")
        ax.set_ylabel("Intensidade Normalizada")
        ax.set_title("XRD: Amostra vs Melhor Referência")
        ax.legend()
        plt.tight_layout()
        plt.show()


def plot_rietveld(resultado: dict) -> None:
    """
    Plota o resultado do refinamento de Rietveld: observado vs calculado + curva de resíduo.

    Args:
        resultado: Dicionário retornado por refinamento_sequencial_oxidos(),
                   com as chaves 'x', 'yobs', 'ycalc', 'diff' e 'wR'.
    """
    x = resultado["x"]
    yobs = resultado["yobs"]
    ycalc = resultado["ycalc"]
    diff = resultado["diff"]
    wR = resultado["wR"]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(12, 7),
        height_ratios=[3, 1],
        sharex=True,
        gridspec_kw={"hspace": 0.05},
    )

    ax1.plot(x, yobs, "k-", label="Observado", linewidth=0.6)
    ax1.plot(x, ycalc, "r-", label="Calculado", linewidth=0.6)
    ax1.set_ylabel("Intensidade")
    ax1.set_title(f"Refinamento de Rietveld — wR = {wR:.2f}%")
    ax1.legend()

    ax2.plot(x, diff, "b-", linewidth=0.5)
    ax2.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax2.set_xlabel("2θ (°)")
    ax2.set_ylabel("Diferença")

    plt.tight_layout()
    plt.show()


def plot_refinamento_com_referencias(
    x: np.ndarray,
    yobs: np.ndarray,
    ycalc: np.ndarray,
    refs_cif: list[str],
    theta: np.ndarray,
    nome_projeto: str = "",
) -> None:
    """
    Plota o refinamento calculado junto com as curvas referenciais simuladas.

    Args:
        x:             Array de ângulos 2θ do refinamento.
        yobs:          Intensidade observada (experimental).
        ycalc:         Intensidade calculada pelo refinamento.
        refs_cif:      Lista de caminhos para os CIFs usados no refinamento.
        theta:         Grid de ângulos 2θ da amostra original (para simulação dos CIFs).
        nome_projeto:  Nome do projeto exibido no título do gráfico.
    """
    yobs_norm = normalizar(yobs)
    ycalc_norm = normalizar(ycalc)

    plt.figure(figsize=(10, 6))
    plt.plot(x, yobs_norm, "k-", label="Observado", linewidth=0.8)
    plt.plot(x, ycalc_norm, "r-", label="Calculado (Rietveld)", linewidth=0.8)

    for ref_cif in refs_cif:
        nome_fase = Path(ref_cif).stem
        try:
            yref = simular_padrao_xrd(ref_cif, theta)
            yref_norm = normalizar(yref)
            plt.plot(theta, yref_norm, "--", label=f"Referência: {nome_fase}", alpha=0.7)
        except Exception as e:
            logger.warning("Erro ao simular referência %s: %s", nome_fase, e)

    plt.xlabel("2θ (°)")
    plt.ylabel("Intensidade Normalizada")
    titulo = f"Refinamento de Rietveld e Referências — {nome_projeto}" if nome_projeto else "Refinamento de Rietveld e Referências"
    plt.title(titulo)
    plt.legend()
    plt.tight_layout()
    plt.show()
