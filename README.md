# ReDifraX

## Sobre

Pipeline de análise de difração de raios X (XRD) que automatiza:

1. **Download de referências** — busca arquivos CIF do banco [Crystallography Open Database (COD)](http://www.crystallography.net/cod/).
2. **Filtro primário** — compara o difratograma experimental com padrões simulados via `pymatgen` usando correlação de Pearson, gerando um ranking de fases candidatas.
3. **Refinamento de Rietveld** — executa refinamento sequencial (escala, background, deslocamento, célula unitária, perfil de pico e posições atômicas) usando [GSAS-II](https://advancedphotonsource.github.io/GSAS-II-tutorials/) via scripting.

### Estrutura do projeto

```
ReDifraX/
├── run.ipynb                          # Notebook principal de execução
├── requirements.txt                   # Dependências Python extras
├── input/                             # Dados experimentais (.txt, .prm)
├── project/                           # Projetos criados em tempo de execução
└── functions/
    ├── Diretories_Downloads.py        # Criação de diretórios e download de CIFs
    ├── Primary_Filter.py              # Simulação XRD e ranking por correlação
    └── Workflow_GSAS2.py              # Refinamento de Rietveld via GSAS-II
```

## Instalacao do ambiente

O projeto usa um unico ambiente (`.venv_gsas2`) que contem o GSAS-II e todas as dependencias Python.

### 1. Clonar o repositorio

```bash
git clone https://github.com/MozarteSS/ReDifraX
cd ReDifraX
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

### 6. Executar

Coloque seu difratograma experimental (formato RRUFF: `2θ, intensidade`) na pasta `input/` e execute o notebook:

```bash
source .venv_gsas2/bin/activate
jupyter notebook run.ipynb
```

O notebook segue o fluxo:

1. Cria o diretório do projeto (`project/<nome>/ref/`).
2. Baixa CIFs de referência do COD (hematita, magnetita, maghemita, goethita, wüstita, ferro metálico).
3. Executa o filtro primário e exibe o ranking de similaridade.
4. Plota o difratograma experimental sobreposto à melhor referência.
5. Executa o refinamento de Rietveld via GSAS-II e reporta os fatores wR/wRb.