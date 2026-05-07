#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARTIFACTS="$SCRIPT_DIR/artifacts"
FORMAT="${1:-svg}"

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

failed=0
for file in "${puml_files[@]}"; do
    name="$(basename "$file" .puml)"
    if plantuml "-t$FORMAT" -o "$ARTIFACTS" "$file"; then
        echo "  ✓ $name.$FORMAT"
    else
        echo "  ✗ $name.$FORMAT (FAILED)" >&2
        failed=$((failed + 1))
    fi
done

echo
if [[ $failed -eq 0 ]]; then
    echo "Done."
else
    echo "Done with $failed failure(s)." >&2
    exit 1
fi
