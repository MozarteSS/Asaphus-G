from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectConfig:
    """Centraliza todos os caminhos de um projeto de análise XRD.

    Exemplo de uso::

        cfg = ProjectConfig("projeto_x")
        cfg.create_dirs()
        # cfg.ref_dir     → projects/projeto_x/ref
        # cfg.results_dir → projects/projeto_x/results
    """

    project_name: str
    base_dir: str = "projects"
    input_dir: str = "inputs"

    @property
    def project_dir(self) -> Path:
        return Path(self.base_dir) / self.project_name

    @property
    def ref_dir(self) -> Path:
        return self.project_dir / "ref"

    @property
    def results_dir(self) -> Path:
        return self.project_dir / "results"

    def create_dirs(self) -> None:
        """Cria os diretórios do projeto se não existirem."""
        self.ref_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
