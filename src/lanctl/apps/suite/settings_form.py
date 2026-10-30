"""Additive form hints for the desktop adapter; validation stays in services."""

from lanctl.core.config import DOCUMENT_DEFAULTS
from lanctl.core.settings_catalog import VALUE_CHOICES, leaves
from lanctl.shared.i18n import t, translate_label


def describe_settings(entries, *, project=False):
    defaults = dict(leaves(DOCUMENT_DEFAULTS))
    result = []
    for entry in entries:
        path, value = entry["path"], entry["value"]
        schema_path = path
        if project and path.startswith("network."):
            from lanctl.core.projects.settings import NETWORK_PATHS

            schema_path = NETWORK_PATHS.get(path.split(".", 1)[1], path)
        default = defaults.get(schema_path, value)
        sample = value if value is not None else default
        kind = (
            "boolean"
            if isinstance(sample, bool) or path == "network.dhcpEnabled"
            else "number"
            if type(sample) in (int, float)
            or path
            in {
                "network.dhcpLeaseTime",
                "monitor.duration",
                "vlan.nativeVlan",
                "vlan.managementVlan",
            }
            else "lines"
            if isinstance(sample, list) and all(isinstance(item, str) for item in sample)
            else "json"
            if isinstance(sample, (dict, list))
            else "text"
        )
        choices = [{"value": item, "label": item} for item in VALUE_CHOICES.get(schema_path, ())]
        if schema_path == "projects.saveMode":
            from lanctl.core.projects.save_policy import available_save_modes

            choices = [
                {
                    "value": item.mode,
                    "label": translate_label(item.description) if item.description else item.mode,
                }
                for item in available_save_modes()
            ]
        elif path == "gui.theme":
            from lanctl.core.gui_preferences import preferences_payload

            choices = [
                {"value": item["id"], "label": item["name"]}
                for item in preferences_payload()["themes"]
            ]
        elif path == "gui.density":
            choices = [
                {"value": "comfortable", "label": t("LANCTL.UI.SCREEN.COMFORTABLE")},
                {"value": "compact", "label": "Compacta"},
            ]
        result.append(
            {
                **entry,
                "readOnly": translate_label(entry.get("readOnly", "")),
                "control": kind,
                "nullable": default is None,
                "choices": choices,
            }
        )
    return result
