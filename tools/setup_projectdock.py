"""Prepara configuración local de ProjectDock sin ejecutar ni autorizar recetas."""

from __future__ import annotations

import argparse
import json
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare(root: Path, python: str, apply: bool = False) -> dict:
    root = root.resolve()
    template = json.loads(
        (ROOT / "repositoryTerminal/projectdock/recipes.json").read_text(encoding="utf-8")
    )
    config = {
        "schema": 1,
        "id": str(uuid.uuid4()),
        "instance_id": str(uuid.uuid4()),
        "name": root.name,
        "languages": ["python"],
        "default_action": "start",
        "default_profile": "development",
        "python": python,
        "trusted": False,
        "portability": "system-dependent",
        "tools": {},
        "logs": {"keep_runs": 100},
        "version": "",
        "environment": {
            "LANCTL_DATA_DIR": "{root}/.project/lanctl-data",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
    }
    report = {
        "root": str(root),
        "apply": apply,
        "python": python,
        "recipes": [item["name"] for item in template],
        "existing_configuration": (root / ".project").exists(),
        "launcher_created": False,
        "trusted": False,
    }
    if not apply:
        return report
    if not root.is_dir():
        raise ValueError("El directorio del proyecto no existe")
    if (root / ".project").exists():
        raise FileExistsError("Ya existe .project; se conserva sin modificaciones")
    if not Path(python).is_file():
        raise ValueError("--python debe indicar un ejecutable existente")
    with tempfile.TemporaryDirectory(prefix=".project-setup-", dir=root) as temporary:
        stage = Path(temporary) / ".project"
        for name in [
            "recipes",
            "profiles",
            "scripts",
            "rules",
            "connectors",
            "logs",
            "state",
            "runtime",
        ]:
            (stage / name).mkdir(parents=True, exist_ok=True)

        def write(path, value):
            path.write_text(
                json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )

        write(stage / "project.json", config)
        write(stage / "profiles/development.json", {"environment": {}, "args": {}, "tools": {}})
        for recipe in template:
            write(stage / "recipes" / (recipe["name"] + ".json"), recipe)
        stage.rename(root / ".project")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--python", default="python")
    parser.add_argument("--apply", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.root, arguments.python, arguments.apply), indent=2))


if __name__ == "__main__":
    main()
