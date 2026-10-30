"""Ayuda navegable de LANWIRE, con la jerarquía visual de LANIP."""

from __future__ import annotations

from dataclasses import dataclass

from rich.text import Text

from lanctl.shared.i18n import t


@dataclass(frozen=True)
class HelpEntry:
    name: str
    arguments: str
    description: str
    usage: str


COMMANDS = (
    HelpEntry("help", "", "LANCTL.UI.TEXT.SHOW_THIS_HELP", "help"),
    HelpEntry(
        "list",
        "[PREFIJO|@GRUPO]",
        "LANCTL.UI.TEXT.LIST_AND_FILTER_PHYSICAL_IDFS",
        "list [PREFIJO|@GRUPO]",
    ),
    HelpEntry(
        "idf list", "[PREFIJO]", "LANCTL.UI.TEXT.LIST_PREFIXES_OR_THEIR_IDFS", "idf list [PREFIJO]"
    ),
    HelpEntry("idf types", "", "LANCTL.UI.TEXT.ENUMERATE_AVAILABLE_PHYSICAL_PROFILES", "idf types"),
    HelpEntry("idf show", "PREFIJO|IDF", "LANCTL.UI.TEXT.QUERY_A_PROFILE_OR_IDF", "idf show RT-00"),
    HelpEntry(
        "idf new",
        "PREFIJO -type TIPO",
        "LANCTL.UI.TEXT.ASSIGN_A_PHYSICAL_PROFILE_TO_A_PREFIX",
        "idf new FB -type wire.fiber",
    ),
    HelpEntry(
        "idf add",
        "IDF [-name NOMBRE]",
        "LANCTL.UI.TEXT.CREATE_AN_IDF_WITH_ITS_PREFIX_PROFILE",
        "idf add FB-00 -name Fibra",
    ),
    HelpEntry(
        "idf edit",
        "IDF CAMPO=VALOR",
        "LANCTL.UI.TEXT.EDIT_DATA_OR_A_PREFIX_PROFILE",
        "idf edit RT-00 alias=Central",
    ),
    HelpEntry(
        "idf delete",
        "IDF",
        "LANCTL.UI.TEXT.DELETE_AN_IDF_WITHOUT_DELETING_ITS_PREFIX",
        "idf delete FB-00",
    ),
    HelpEntry("prefix", "list|show|set|delete", "LANCTL.UI.TEXT.MANAGE_LETTER_SETS", "prefix list"),
    HelpEntry(
        "add",
        "PREFIJO [-more N]",
        "LANCTL.UI.TEXT.GENERATE_ONE_OR_MORE_AVAILABLE_IDFS",
        "add FB -more 3",
    ),
    HelpEntry(
        "reserve",
        "IDF [CLAVE=VALOR]",
        "LANCTL.UI.TEXT.RESERVE_AN_EXACT_IDENTIFIER",
        "reserve FB-09",
    ),
    HelpEntry("show", "[IDF]", "LANCTL.UI.TEXT.OPEN_AN_ELEMENT_S_DATA", "show FB-00"),
    HelpEntry(
        "element",
        "IDF [CAMPO=VALOR]",
        "LANCTL.UI.TEXT.QUERY_OR_EDIT_DATA_AND_PORTS",
        "element RT-00 ports=2",
    ),
    HelpEntry("graph", "(map)", "LANCTL.UI.TEXT.DRAW_THE_PHYSICAL_TOPOLOGY", "graph"),
    HelpEntry("delete", "IDF", "LANCTL.UI.TEXT.DELETE_AN_IDF_AND_CLEAR_ITS_LINKS", "delete FB-00"),
    HelpEntry("seed", "", "LANCTL.UI.TEXT.LOAD_THE_DEMONSTRATION_TOPOLOGY", "seed"),
    HelpEntry("clear", "", "LANCTL.UI.TEXT.CLEAR_THE_TUI_CLI_OUTPUT", "clear"),
    HelpEntry("exit", "(quit)", "LANCTL.UI.TEXT.CLOSE_LANWIRE", "exit"),
)

KEYS = (
    "LANCTL.UI.TEXT.SWITCH_BETWEEN_COMMANDS_DETAILS_AND_KEYS",
    "LANCTL.UI.TEXT.SELECT_A_COMMAND_OR_SCROLL_CONTENT",
    "LANCTL.UI.TEXT.PGUP_PGDN_MOVE_THROUGH_THE_LIST_OR_CONTENT",
    "LANCTL.UI.TEXT.HOME_END_GO_TO_THE_FIRST_OR_LAST_COMMAND",
    "LANCTL.UI.TEXT.ENTER_OPEN_DETAILS_FOR_THE_SELECTED_COMMAND",
    "LANCTL.UI.TEXT.TAB_PREPARE_THE_SELECTED_COMMAND_AT_THE_PROMPT",
    "LANCTL.UI.TEXT.F1_ESC_CLOSE_THIS_WINDOW",
    "",
    "LANCTL.UI.TEXT.IN_THE_INVENTORY",
    "LANCTL.UI.TEXT.TAB_SWITCH_ELEMENTS_WIRE_ALL",
    "LANCTL.UI.TEXT.ENTER_OPEN_THE_SELECTED_ELEMENT",
    "LANCTL.UI.TEXT.F3_FOLLOW_THE_SELECTED_CABLE_OR_ENDPOINT",
    "LANCTL.UI.TEXT.DELETE_DELETE_THE_ELEMENT_WITH_CONFIRMATION",
    "LANCTL.UI.TEXT.F7_EXTENSIONS",
    "LANCTL.UI.TEXT.F9_ACTIVE_PHYSICAL_DATABASE",
    "LANCTL.UI.TEXT.F12_LANWIRE_SETTINGS",
    "LANCTL.UI.TEXT.CTRL_S_SAVE_PREFERENCES",
    "LANCTL.UI.TEXT.CTRL_C_COPY_IDF",
    "LANCTL.UI.TEXT.CTRL_J_COPY_JSON",
    "LANCTL.UI.TEXT.CTRL_H_HISTORY",
    "LANCTL.UI.TEXT.CTRL_Q_QUIT",
)


def help_view(width: int, height: int, tab: int, selected: int, scroll: int) -> Text:
    """Compone la zona interior del modal, ajustada a la terminal actual."""
    width = max(20, width)
    height = max(2, height)
    text = Text(no_wrap=True, overflow="crop")
    for index, label in enumerate(
        (
            t("LANCTL.UI.TEXT.COMMANDS"),
            t("LANCTL.UI.TEXT.DETAILS_426234E7"),
            t("LANCTL.UI.TEXT.KEYS"),
        )
    ):
        if index:
            text.append("   ")
        text.append(f" {label} ", style="black on bright_cyan" if tab == index else "bright_cyan")
    text.append("\n" + "─" * width, style="grey50")

    if tab == 0:
        visible = max(0, height - 2)
        start = max(0, min(scroll, max(0, len(COMMANDS) - visible)))
        name_width = min(22, max(12, width // 5))
        args_width = min(28, max(12, width // 4))
        for index in range(start, min(len(COMMANDS), start + visible)):
            entry = COMMANDS[index]
            text.append("\n")
            text.append("▸ " if index == selected else "  ", style="bright_cyan")
            text.append(
                f"{entry.name:<{name_width}}",
                style="bright_cyan" if index == selected else "bright_white",
            )
            text.append(f"{entry.arguments:<{args_width}}", style="bright_white")
            text.append(
                t(entry.description), style="bright_cyan" if index == selected else "bright_white"
            )
    else:
        entry = COMMANDS[selected]
        lines = (
            (
                f"COMANDO  lanwire {entry.name}",
                "",
                t(entry.description),
                "",
                t("LANCTL.UI.TEXT.USAGE"),
                f"  lanwire {entry.usage}",
                "",
                t("LANCTL.UI.TEXT.THE_SAME_COMMAND_IS_AVAILABLE_AT_THE_LANWIRE_PROMPT"),
                t("LANCTL.UI.TEXT.TAB_PREPARES_IT_AT_THE_PROMPT"),
            )
            if tab == 1
            else tuple(t(key) if key else "" for key in KEYS)
        )
        for line in lines[scroll : scroll + max(0, height - 2)]:
            text.append("\n")
            text.append(
                line, style="bright_cyan" if line in {"USO", "EN EL INVENTARIO"} else "bright_white"
            )
    return text
