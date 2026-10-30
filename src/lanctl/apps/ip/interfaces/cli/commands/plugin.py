from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from colorama import Fore, Style

from lanctl.core.console import ok
from lanctl.core.plugins.manager import get_plugin_manager
from lanctl.core.plugins.package import build_package, verify_package
from lanctl.core.resources import bundled_path
from lanctl.shared.i18n import t


def register_plugin_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "plugin",
        aliases=["plugins", "addon", "addons"],
        help=t("LANCTL.UI.HELP.MANAGE_UNIFIED_LANCTL_LCP_PLUGINS"),
    )
    actions = command.add_subparsers(dest="plugin_action", metavar="ACCIÓN", required=True)
    actions.add_parser("list", help=t("LANCTL.UI.HELP.LIST_INSTALLED_PLUGINS")).set_defaults(
        plugin_handler=_list
    )
    actions.add_parser(
        "catalog", help=t("LANCTL.UI.HELP.SHOW_THE_BUNDLED_OFFICIAL_CATALOG")
    ).set_defaults(plugin_handler=_catalog)
    info = actions.add_parser("info", help=t("LANCTL.UI.HELP.SHOW_MANIFEST_PERMISSIONS_AND_STATE"))
    info.add_argument("plugin_id", help=t("LANCTL.UI.HELP.STABLE_PLUGIN_IDENTIFIER"))
    info.set_defaults(plugin_handler=_info)
    install = actions.add_parser(
        "install", help=t("LANCTL.UI.HELP.VERIFY_AND_INSTALL_A_DISABLED_LCP_PACKAGE")
    )
    install.add_argument("file", help=t("LANCTL.UI.HELP.PACKAGE_FILE_WITH_THE_LCP_EXTENSION"))
    install.set_defaults(plugin_handler=_install)
    enable = actions.add_parser(
        "enable", help=t("LANCTL.UI.HELP.GRANT_PERMISSIONS_AND_ENABLE_A_PLUGIN")
    )
    enable.add_argument("plugin_id", help=t("LANCTL.UI.HELP.INSTALLED_PLUGIN_IDENTIFIER"))
    enable.add_argument(
        "--grant",
        nargs="*",
        default=None,
        metavar="PERMISO",
        help=t("LANCTL.UI.HELP.SPECIFIC_PERMISSIONS_TO_GRANT"),
    )
    enable.add_argument(
        "--grant-all", action="store_true", help=t("LANCTL.UI.HELP.GRANT_ALL_REQUESTED_PERMISSIONS")
    )
    enable.add_argument(
        "--trust",
        action="store_true",
        help=t("LANCTL.UI.HELP.AUTHORIZE_TRUSTED_CODE_WITHIN_THE_PROCESS"),
    )
    enable.set_defaults(plugin_handler=_enable)
    for name, handler, help_text in (
        ("disable", _disable, "Desactiva el complemento."),
        ("reload", _reload, "Recarga un complemento activo."),
        ("uninstall", _uninstall, "Desinstala el complemento."),
    ):
        item = actions.add_parser(name, help=help_text)
        item.add_argument("plugin_id", help=t("LANCTL.UI.HELP.INSTALLED_PLUGIN_IDENTIFIER"))
        item.set_defaults(plugin_handler=handler)
    verify = actions.add_parser("verify", help=t("LANCTL.UI.HELP.VERIFY_A_LCP_OR_INSTALLED_PLUGIN"))
    verify.add_argument(
        "target", help=t("LANCTL.UI.HELP.INSTALLED_IDENTIFIER_OR_PATH_TO_A_LCP_FILE")
    )
    verify.set_defaults(plugin_handler=_verify)
    permissions = actions.add_parser(
        "permissions", help=t("LANCTL.UI.HELP.SHOW_REQUESTED_AND_GRANTED_PERMISSIONS")
    )
    permissions.add_argument("plugin_id", help=t("LANCTL.UI.HELP.INSTALLED_PLUGIN_IDENTIFIER"))
    permissions.set_defaults(plugin_handler=_permissions)
    revoke = actions.add_parser(
        "revoke", help=t("LANCTL.UI.HELP.REVOKE_A_PLUGIN_S_PERMISSIONS_AND_TRUST")
    )
    revoke.add_argument("plugin_id", help=t("LANCTL.UI.HELP.INSTALLED_PLUGIN_IDENTIFIER"))
    revoke.add_argument(
        "permissions",
        nargs="*",
        metavar="PERMISO",
        help=t("LANCTL.UI.HELP.LEAVE_EMPTY_TO_REVOKE_ALL_PERMISSIONS"),
    )
    revoke.set_defaults(plugin_handler=_revoke)
    publisher = actions.add_parser(
        "publisher", help=t("LANCTL.UI.HELP.MANAGE_ED25519_FINGERPRINTS_OF_TRUSTED_LCP_PUBLISHERS")
    )
    publisher_actions = publisher.add_subparsers(
        dest="publisher_action", metavar="ACCIÓN", required=True
    )
    publisher_actions.add_parser(
        "list", help=t("LANCTL.UI.HELP.LIST_TRUSTED_PUBLISHERS")
    ).set_defaults(plugin_handler=_publisher_list)
    trust_publisher = publisher_actions.add_parser(
        "trust", help=t("LANCTL.UI.HELP.TRUST_THE_SIGNATURE_CONTAINED_IN_AN_LCP_PACKAGE")
    )
    trust_publisher.add_argument("file", help=t("LANCTL.UI.HELP.SIGNED_AND_VERIFIED_LCP_PACKAGE"))
    trust_publisher.add_argument(
        "--name", default="", help=t("LANCTL.UI.HELP.DESCRIPTIVE_PUBLISHER_NAME")
    )
    trust_publisher.set_defaults(plugin_handler=_publisher_trust)
    revoke_publisher = publisher_actions.add_parser(
        "revoke", help=t("LANCTL.UI.HELP.REVOKE_A_PUBLISHER_FINGERPRINT")
    )
    revoke_publisher.add_argument(
        "fingerprint", help=t("LANCTL.UI.HELP.FULL_ED25519_SHA_256_FINGERPRINT")
    )
    revoke_publisher.set_defaults(plugin_handler=_publisher_revoke)
    extensions = actions.add_parser(
        "extensions", help=t("LANCTL.UI.HELP.LIST_EXTENSIONS_FOR_CLI_TUI_AND_THE_FUTURE_GUI")
    )
    extensions.add_argument("--type", help=t("LANCTL.UI.HELP.FILTER_BY_UNIFIED_EXTENSION_TYPE"))
    extensions.set_defaults(plugin_handler=_extensions)
    pack = actions.add_parser("pack", help=t("LANCTL.UI.HELP.BUILD_A_LCP_PACKAGE_FROM_A_DIRECTORY"))
    pack.add_argument("directory", help=t("LANCTL.UI.HELP.SOURCE_DIRECTORY_CONTAINING_PLUGIN_INFO"))
    pack.add_argument("output", help=t("LANCTL.UI.HELP.OUTPUT_LCP_FILE"))
    pack.add_argument(
        "--force",
        action="store_true",
        help=t("LANCTL.UI.HELP.OVERWRITE_THE_EXISTING_OUTPUT_PACKAGE"),
    )
    pack.add_argument(
        "--signing-key", help=t("LANCTL.UI.HELP.ED25519_PEM_PRIVATE_KEY_FOR_SIGNING_THE_LCP")
    )
    pack.set_defaults(plugin_handler=_pack)
    command.set_defaults(handler=lambda args: args.plugin_handler(args))


def _list(args) -> int:
    values = get_plugin_manager().list()
    print(
        f"{Style.BRIGHT}{Fore.CYAN}{'ID':<30} {'VERSION':<14} {'STATE':<14} TYPES{Style.RESET_ALL}"
    )
    print("-" * 90)
    for plugin in values:
        print(
            f"{plugin.manifest.plugin_id:<30} {plugin.manifest.version:<14} {plugin.state.value:<14} {','.join(plugin.manifest.capabilities)}"
        )
    if not values:
        print(t("LANCTL.UI.PROMPT.NO_PLUGINS_INSTALLED"))
    return 0


def _catalog(args) -> int:
    document = json.loads(bundled_path("bundled/plugin-catalog.json").read_text(encoding="utf-8"))
    print(json.dumps(document, ensure_ascii=False, indent=2))
    return 0


def _info(args) -> int:
    plugin = get_plugin_manager().get(args.plugin_id)
    data = asdict(plugin.manifest)
    data.update(
        {
            "state": plugin.state.value,
            "granted": sorted(plugin.granted),
            "trusted": plugin.trusted,
            "error": plugin.error,
            "signature": plugin.signature,
            "path": str(plugin.path),
        }
    )
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _install(args) -> int:
    inspected = verify_package(args.file)
    requested = inspected["manifest"].permissions
    print(t("LANCTL.UI.PROMPT.REQUESTED_PERMISSIONS_BEFORE_INSTALLATION"))
    print(" " + (", ".join(requested) if requested else t("LANCTL.UI.VALUE.NONE")))
    print(t("LANCTL.UI.DETAIL.SIGNATURE_VALUE", value0=f"{inspected['signature']}"))
    plugin = get_plugin_manager().install(args.file)
    ok(
        t("LANCTL.UI.STATUS.PLUGIN_INSTALLED"),
        t(
            "LANCTL.UI.SUMMARY.VALUE_VALUE_DISABLED",
            value0=f"{plugin.manifest.plugin_id}",
            value1=f"{plugin.manifest.version}",
        ),
    )
    print(t("LANCTL.UI.PROMPT.ENABLE_IT_WITH_LANCTL_PLUGIN_ENABLE_ID_GRANT_ALL"))
    return 0


def _enable(args) -> int:
    manager = get_plugin_manager()
    plugin = manager.get(args.plugin_id)
    grants = (
        set(plugin.manifest.permissions)
        if args.grant_all
        else (set(args.grant) if args.grant is not None else set(plugin.granted))
    )
    manager.enable(args.plugin_id, grant=grants, trusted=args.trust)
    ok(t("LANCTL.UI.STATUS.PLUGIN_ACTIVE"), args.plugin_id)
    return 0


def _disable(args) -> int:
    get_plugin_manager().disable(args.plugin_id)
    ok(t("LANCTL.UI.STATUS.PLUGIN_DISABLED"), args.plugin_id)
    return 0


def _reload(args) -> int:
    get_plugin_manager().reload(args.plugin_id)
    ok(t("LANCTL.UI.STATUS.PLUGIN_RELOADED"), args.plugin_id)
    return 0


def _uninstall(args) -> int:
    get_plugin_manager().uninstall(args.plugin_id)
    ok(t("LANCTL.UI.STATUS.PLUGIN_REMOVED"), args.plugin_id)
    return 0


def _verify(args) -> int:
    result = get_plugin_manager().verify(args.target)
    manifest = result["manifest"]
    ok(t("LANCTL.UI.STATUS.LCP_VALID"), f"{manifest.plugin_id} {manifest.version}")
    if result.get("checksum"):
        print(f" SHA-256 : {result['checksum']}")
    if result.get("signature"):
        print(t("LANCTL.UI.DETAIL.SIGNATURE_VALUE_B2E0957F", value0=f"{result['signature']}"))
    return 0


def _permissions(args) -> int:
    plugin = get_plugin_manager().get(args.plugin_id)
    granted = set(plugin.granted)
    for permission in plugin.manifest.permissions:
        print(f" {'O' if permission in granted else 'X'}  {permission}")
    return 0


def _revoke(args) -> int:
    permissions = set(args.permissions) if args.permissions else None
    get_plugin_manager().revoke(args.plugin_id, permissions)
    ok(t("LANCTL.UI.STATUS.PERMISSIONS_REVOKED"), args.plugin_id)
    return 0


def _publisher_list(args) -> int:
    print(json.dumps(get_plugin_manager().publishers.list(), ensure_ascii=False, indent=2))
    return 0


def _publisher_trust(args) -> int:
    entry = get_plugin_manager().publishers.trust_package(args.file, args.name)
    ok(t("LANCTL.UI.STATUS.TRUSTED_PUBLISHER"), entry["name"])
    print(t("LANCTL.UI.DETAIL.FINGERPRINT_VALUE", value0=f"{entry['fingerprint']}"))
    return 0


def _publisher_revoke(args) -> int:
    if not get_plugin_manager().publishers.revoke(args.fingerprint):
        raise ValueError("huella de editor no encontrada")
    ok(t("LANCTL.UI.STATUS.PUBLISHER_REVOKED"), args.fingerprint)
    return 0


def _extensions(args) -> int:
    values = get_plugin_manager().extensions.list(args.type)
    print(f"{'TYPE':<20} {'ID':<36} OWNER")
    print("-" * 90)
    for item in values:
        print(f"{item.extension_type:<20} {item.extension_id:<36} {item.owner}")
    return 0


def _pack(args) -> int:
    result = build_package(
        args.directory, args.output, overwrite=args.force, signing_key=args.signing_key
    )
    ok(t("LANCTL.UI.STATUS.LCP_CREATED"), result["path"])
    print(f" SHA-256 : {result['checksum']}")
    print(t("LANCTL.UI.DETAIL.SIGNATURE_VALUE_B2E0957F", value0=f"{result['signature']}"))
    return 0
