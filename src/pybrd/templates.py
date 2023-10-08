from pathlib import Path

from loguru import logger


class Templates:
    def __init__(self, path: str) -> None:
        self.path = Path(path)

    def render(self, template: str, **kwargs) -> str:
        template_path = self.path / template
        with template_path.open() as fp:
            return fp.read().format(**kwargs)
