# Cargar con: source /ruta/al/checkout/packaging/bash/run.bash
_LANCTL_RUN_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
_lanctl_run_complete() {
    local python=python3 candidate
    for candidate in "$_LANCTL_RUN_ROOT/.venv/bin/python" "$_LANCTL_RUN_ROOT/.venv311/bin/python"; do
        if [[ -x $candidate ]] && "$candidate" -c 'import sys' >/dev/null 2>&1; then
            python=$candidate
            break
        fi
    done
    COMPREPLY=()
    while IFS= read -r candidate; do
        [[ -n $candidate ]] && COMPREPLY+=("$candidate")
    done < <("$python" "$_LANCTL_RUN_ROOT/tools/complete_run.py" "${COMP_WORDS[@]:1:COMP_CWORD}" 2>/dev/null)
}
complete -o bashdefault -o default -F _lanctl_run_complete run run.sh ./run.sh "$_LANCTL_RUN_ROOT/run.sh"
