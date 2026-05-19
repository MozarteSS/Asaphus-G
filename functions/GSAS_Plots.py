import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from functions.Primary_Filter import normalizar, simular_padrao_xrd

logger = logging.getLogger(__name__)

title_fontsize = 14
xlabel_fontsize = 14
ylabel_fontsize = 14
tick_labelsize = 14

COR_EXPERIMENTAL = "#130909"
COR_CALCULADO = "#e03b3b"
COR_DIFERENCA = "#037a09"
COR_REFERENCIA = "#0c2cdf"


def _marcar_picos(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    color: str,
    prominence: float = 0.05,
    markersize: int = 6,
) -> None:
    peaks, _ = find_peaks(y, prominence=prominence)
    if len(peaks):
        ax.scatter(x[peaks], y[peaks], color=color, s=markersize ** 2, zorder=5, linewidths=0)


def _save_figure(fig: plt.Figure, save_path: Path | str, nome_projeto: str, suffix: str) -> None:
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    prefix = f"{nome_projeto}_" if nome_projeto else ""
    img_file = save_path / f"{prefix}{suffix}.png"
    fig.savefig(img_file, dpi=150, bbox_inches="tight")
    logger.info("Gráfico salvo em %s", img_file)


def plot_filtro_primario(
    theta: np.ndarray,
    amostra_norm: np.ndarray,
    df: pd.DataFrame,
    top_n: int = 1,
) -> None:
    """
    Plota a amostra experimental contra as melhores referências do filtro primário.

    Args:
        theta:        Array de ângulos 2θ da amostra.
        amostra_norm: Intensidade normalizada da amostra experimental.
        df:           DataFrame retornado por primary_filter(), ordenado por score.
        top_n:        Número de melhores referências a plotar (padrão: 1).
    """
    for _, row in df.head(top_n).iterrows():
        nome = row['nome']
        score = row['score']
        ref_int_norm = row['ref_int_norm']

        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(theta, amostra_norm, label="Amostra (experimental)", linewidth=1.2, color=COR_EXPERIMENTAL)
        _marcar_picos(ax, theta, amostra_norm, COR_EXPERIMENTAL)
        ax.plot(
            theta, ref_int_norm,
            label=f"Referência: {nome} (score={score:.2%})",
            linewidth=1.2, alpha=0.8, color=COR_REFERENCIA,
        )
        _marcar_picos(ax, theta, ref_int_norm, COR_REFERENCIA)
        ax.set_xlabel("2θ (°)", fontsize=xlabel_fontsize)
        ax.set_ylabel("Intensidade Normalizada", fontsize=ylabel_fontsize)
        ax.set_title("XRD: Amostra vs Melhor Referência", fontsize=title_fontsize)
        ax.tick_params(axis="both", labelsize=tick_labelsize)
        ax.legend()
        fig.tight_layout()
        plt.show()
        plt.close(fig)


def plot_rietveld(
    resultado: dict,
    nome_projeto: str = "",
    save_path: Path | str | None = None,
    refs_cif: list[str] | None = None,
    theta: np.ndarray | None = None,
) -> None:
    """
    Plota o resultado do refinamento de Rietveld: Experimental vs calculado + curva de resíduo.

    Args:
        resultado:    Dicionário retornado por refinamento_sequencial_oxidos(),
                      com as chaves 'x', 'yobs', 'ycalc', 'diff' e 'wR'.
        nome_projeto: Nome do projeto exibido no título do gráfico.
        save_path:    Diretório onde a imagem será salva (PNG). Se None, não salva.
        refs_cif:     Lista de caminhos para CIFs a simular como referência (opcional).
        theta:        Grid de ângulos 2θ para simulação dos CIFs (obrigatório se refs_cif fornecido).
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
    ax1.tick_params(axis="both", labelsize=tick_labelsize)
    ax2.tick_params(axis="both", labelsize=tick_labelsize)

    ax1.plot(x, yobs, "-", label="Experimental", linewidth=1.1, color=COR_EXPERIMENTAL)
    ax1.plot(x, ycalc, "-", label="Calculado", linewidth=1.1, color=COR_CALCULADO)
    _marcar_picos(ax1, x, ycalc, COR_CALCULADO)

    if refs_cif and theta is not None:
        for ref_cif in refs_cif:
            nome_fase = Path(ref_cif).stem
            try:
                yref = simular_padrao_xrd(ref_cif, theta)
                yref_norm = normalizar(yref)
                ax1.plot(theta, yref_norm, "--", label=f"Referência: {nome_fase}", alpha=0.7, color=COR_REFERENCIA)
                _marcar_picos(ax1, theta, yref_norm, COR_REFERENCIA)
            except Exception as e:
                logger.warning("Erro ao simular referência %s: %s", nome_fase, e)

    ax1.set_ylabel("Intensidade", fontsize=ylabel_fontsize)
    titulo = f"Refinamento de Rietveld — wR = {wR:.2f}%" if not nome_projeto else f"Refinamento de Rietveld — {nome_projeto} — wR = {wR:.2f}%"
    ax1.set_title(titulo, fontsize=title_fontsize)
    ax1.legend()

    ax2.plot(x, diff, "-", linewidth=0.5, color=COR_DIFERENCA)
    ax2.axhline(np.median(diff), color="gray", linewidth=0.5, linestyle="--")
    ax2.set_xlabel("2θ (°)", fontsize=xlabel_fontsize)
    ax2.set_ylabel("Diferença", fontsize=ylabel_fontsize)

    fig.tight_layout()

    if save_path is not None:
        _save_figure(fig, save_path, nome_projeto, "rietveld")

    plt.show()
    plt.close(fig)


def plot_refinamento_com_referencias(
    x: np.ndarray,
    yobs: np.ndarray,
    ycalc: np.ndarray,
    refs_cif: list[str],
    theta: np.ndarray,
    nome_projeto: str = "",
    save_path: Path | str | None = None,
    diff_ylim: tuple[float, float] | None = None,
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
        save_path:     Diretório onde a imagem será salva (PNG). Se None, não salva.
        diff_ylim:     Limites do eixo y do painel de diferença, ex: (-0.05, 0.05). Se None, automático.
    """
    ymin, ymax = yobs.min(), yobs.max()
    rng = ymax - ymin if ymax != ymin else 1.0
    yobs_norm = (yobs - ymin) / rng
    ycalc_norm = (ycalc - ymin) / rng
    diff = yobs_norm - ycalc_norm

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 8),
        height_ratios=[3, 1],
        sharex=True,
        gridspec_kw={"hspace": 0.05},
    )

    ax1.plot(x, yobs_norm, "-", label="Experimental", linewidth=1.2, color=COR_EXPERIMENTAL)
    ax1.plot(x, ycalc_norm, "-", label="Calculated (Rietveld)", linewidth=1.5, color=COR_CALCULADO)
    _marcar_picos(ax1, x, ycalc_norm, COR_CALCULADO)

    for ref_cif in refs_cif:
        nome_fase = Path(ref_cif).stem
        try:
            yref = simular_padrao_xrd(ref_cif, theta)
            yref_norm = normalizar(yref)
            ax1.plot(theta, yref_norm, "--", label=f"Reference: {nome_fase}", alpha=0.7, color=COR_REFERENCIA)
            _marcar_picos(ax1, theta, yref_norm, COR_REFERENCIA)
        except Exception as e:
            logger.warning("Erro ao simular referência %s: %s", nome_fase, e)

    titulo = f"Rietveld Refinement — {nome_projeto}" if nome_projeto else "Rietveld Refinement"
    ax1.set_title(titulo, fontsize=title_fontsize)
    ax1.set_ylabel("Normalized Intensity", fontsize=ylabel_fontsize)
    ax1.tick_params(axis="both", labelsize=tick_labelsize)
    ax1.legend()

    ax2.plot(x, diff, "-", linewidth=0.5, color=COR_DIFERENCA)
    ax2.axhline(np.median(diff), color="gray", linewidth=0.5, linestyle="--")
    if diff_ylim is not None:
        ax2.set_ylim(diff_ylim)
    ax2.set_xlabel("2θ (°)", fontsize=xlabel_fontsize)
    ax2.set_ylabel("Difference", fontsize=ylabel_fontsize)
    ax2.tick_params(axis="both", labelsize=tick_labelsize)

    fig.tight_layout()

    if save_path is not None:
        _save_figure(fig, save_path, nome_projeto, "refinamento_com_referencias")

    plt.show()
    plt.close(fig)
