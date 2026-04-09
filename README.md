# README

## Instalacao do ambiente

O projeto usa um unico ambiente (`.venv_gsas2`) que contem o GSAS-II e todas as dependencias Python.

### 1. Clonar o repositorio

```bash
git clone <URL_DO_REPOSITORIO>
cd analise_drx
```

### 2. Pre-requisitos

No Linux, garanta que `curl` esteja disponivel:

```bash
sudo apt update
sudo apt install -y curl
```

### 3. Instalar GSAS-II (cria o ambiente `.venv_gsas2`)

O instalador do GSAS-II cria um ambiente conda completo com Python 3.13:

```bash
g2="https://github.com/AdvancedPhotonSource/GSAS-II-buildtools/releases/download/v1.0.1/gsas2main-Latest-Linux-x86_64.sh"
install_loc="$(pwd)/.venv_gsas2"
curl -L "$g2" -o /tmp/g2.sh
bash /tmp/g2.sh -b -p "$install_loc"
```

### 4. Ativar ambiente e instalar dependencias extras

```bash
source .venv_gsas2/bin/activate
pip install -r requirements.txt
```

### 5. Verificacao pos-instalacao

```bash
source .venv_gsas2/bin/activate
python --version
PYTHONPATH="./.venv_gsas2/GSAS-II" python -c "from GSASII.GSASIIscriptable import G2Project; print('GSAS-II OK')"
python -c "import pandas; import scipy; print('pandas/scipy OK')"
```

### 6. Executar scripts

```bash
source .venv_gsas2/bin/activate

# Primary Filter
python Primary_Filter.py

# Workflow GSAS-II
PYTHONPATH="./.venv_gsas2/GSAS-II" python Workflow_GSAS-II.py
```