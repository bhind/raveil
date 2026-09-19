#!/bin/bash
# Bounded canonical readonly dependency tree. No links or special files.
set -euo pipefail
root=${1:-/root/.cache}
test -d "$root" && test ! -L "$root"
manifest=$(mktemp)
paths=$(mktemp)
trap 'rm -f "$manifest" "$paths"' EXIT
find "$root" -mindepth 1 -print0 | LC_ALL=C sort -z > "$paths"
count=0; total=0
while IFS= read -r -d '' path; do
  count=$((count + 1)); test "$count" -le 2048
  relative=${path#"$root"/}
  test "${#relative}" -le 4096
  case "$relative" in *$'\n'*|*$'\t'*) exit 2;; esac
  test ! -L "$path"
  if test -d "$path"; then
    printf 'd\t%s\t%s\n' "$relative" "$(stat -c '%a' "$path")" >> "$manifest"
  elif test -f "$path"; then
    before=$(stat -c '%s %h %a %i %Y %Z' "$path")
    read -r size links mode rest <<< "$before"
    test "$links" = 1; test "$size" -le 268435456
    total=$((total + size)); test "$total" -le 536870912
    digest=$(sha256sum "$path" | cut -d ' ' -f 1)
    test "$before" = "$(stat -c '%s %h %a %i %Y %Z' "$path")"
    printf 'f\t%s\t%s\t%s\t%s\n' "$relative" "$mode" "$size" "$digest" >> "$manifest"
  else
    exit 2
  fi
done < "$paths"
sha256sum "$manifest" | cut -d ' ' -f 1
