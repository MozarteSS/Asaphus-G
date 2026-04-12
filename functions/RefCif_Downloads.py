import os
import time
import logging
import requests

logger = logging.getLogger(__name__)

COD_BASE_URL = "http://www.crystallography.net/cod"
DOWNLOAD_TIMEOUT = 30   # segundos por tentativa
MAX_RETRIES = 3
RETRY_DELAY = 2         # segundos entre tentativas


def _is_valid_cif(content: bytes) -> bool:
    """Verifica se o conteúdo baixado é um CIF válido."""
    try:
        text = content.decode("utf-8", errors="ignore")
        return "data_" in text and "_cell_length_a" in text
    except Exception:
        return False


def cif_download(name: str, cod_id: int, dir_ref: str) -> bool:
    """
    Baixa um arquivo CIF do COD com timeout e retries automáticos.

    Args:
        name:    Nome da fase (usado como nome do arquivo .cif salvo).
        cod_id:  ID numérico do COD (Crystallography Open Database).
        dir_ref: Diretório de destino para o arquivo baixado.

    Returns:
        True se o download foi bem-sucedido, False caso contrário.
    """
    url = f"{COD_BASE_URL}/{cod_id}.cif"
    dest = f"{dir_ref}/{name}.cif"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
            if response.status_code == 200:
                if not _is_valid_cif(response.content):
                    logger.warning("COD %s (%s): conteúdo inválido — não é um CIF reconhecível.", cod_id, name)
                    return False
                with open(dest, "wb") as f:
                    f.write(response.content)
                logger.info("COD %s (%s): baixado com sucesso.", cod_id, name)
                return True
            else:
                logger.warning(
                    "COD %s (%s): HTTP %d (tentativa %d/%d).",
                    cod_id, name, response.status_code, attempt, MAX_RETRIES,
                )
        except requests.exceptions.Timeout:
            logger.warning("COD %s (%s): timeout (tentativa %d/%d).", cod_id, name, attempt, MAX_RETRIES)
        except requests.exceptions.RequestException as e:
            logger.warning(
                "COD %s (%s): erro de rede — %s (tentativa %d/%d).",
                cod_id, name, e, attempt, MAX_RETRIES,
            )

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    logger.error("COD %s (%s): falhou após %d tentativas.", cod_id, name, MAX_RETRIES)
    return False
