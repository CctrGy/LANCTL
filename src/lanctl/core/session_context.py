"""Versioned, one-shot local launch context; contains paths, never credentials."""

import json
import os

ENVIRONMENT_KEY = "LANCTL_SESSION_CONTEXT"


def child_environment(launcher, config, environment=None):
    from lanctl.core.session import PROJECT_KEYS

    result = dict(os.environ if environment is None else environment)
    result[ENVIRONMENT_KEY] = json.dumps(
        {
            "schemaVersion": 1,
            "launcher": launcher,
            "config": {key: config.get(key) for key in PROJECT_KEYS},
        },
        ensure_ascii=False,
    )
    return result


def consume_context(launcher, config):
    from lanctl.core.session import PROJECT_KEYS

    encoded = os.environ.get(ENVIRONMENT_KEY, "")
    if not encoded:
        return config
    payload = json.loads(encoded)
    if payload.get("schemaVersion") != 1 or not isinstance(payload.get("config"), dict):
        raise ValueError("Contexto de lanzamiento no compatible")
    if payload.get("launcher") != launcher:
        return config
    os.environ.pop(ENVIRONMENT_KEY, None)
    values = payload["config"]
    if set(values) - PROJECT_KEYS or any(
        not isinstance(value, (str, dict, type(None))) for value in values.values()
    ):
        raise ValueError("Contexto de proyecto no válido")
    # ConfigSnapshot must retain its canonical document for subsequent saves.
    from copy import deepcopy

    replacement = deepcopy(config)
    replacement.update(values)
    return replacement
