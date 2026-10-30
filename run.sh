#!/bin/sh
# Lanzador de desarrollo de LANCTL para Linux.
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1

foreground=false
if [ "${1-}" = "--foreground" ]; then
    foreground=true
    shift
fi
case "${1-}" in
    -help) shift; set -- --help "$@" ;;
    -version) shift; set -- --version "$@" ;;
esac

python=python3
for candidate in "$project_dir/.venv/bin/python" "$project_dir/.venv311/bin/python"; do
    if [ -x "$candidate" ] && "$candidate" -c 'import sys' >/dev/null 2>&1; then
        python=$candidate
        break
    fi
done

mode=command
for argument do
    case "$argument" in
        --gui) mode=gui ;;
    esac
done
for argument do
    case "$argument" in
        --help|-h|/?|--version) mode=command ;;
    esac
done
if [ "$foreground" = true ] || [ "$mode" = command ]; then
    exec "$python" "$project_dir/lanctl.py" "$@"
fi

# La GUI queda separada, sin terminal adicional ni archivos de salida propios.
nohup setsid -- "$python" "$project_dir/lanctl.py" "$@" </dev/null >/dev/null 2>&1 &
