#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS="$SCRIPT_DIR/artifacts"
FORMAT="${1:-png}"

case "$FORMAT" in
    png|svg|eps|pdf) ;;
    *) echo "Usage: $0 [png|svg|eps|pdf]" >&2; exit 1 ;;
esac

shopt -s nullglob
puml_files=("$ARTIFACTS"/*.puml)

if [[ ${#puml_files[@]} -eq 0 ]]; then
    echo "No .puml files found in $ARTIFACTS" >&2
    exit 1
fi

echo "Rendering ${#puml_files[@]} diagram(s) as $FORMAT → $ARTIFACTS/"
echo

for file in "${puml_files[@]}"; do
    name="$(basename "$file" .puml)"
    plantuml "-t$FORMAT" -o "$ARTIFACTS" "$file"
    echo "  ✓ $name.$FORMAT"
done

echo
echo "Done."
