#!/bin/bash
# Host-functional tests inside the existing offline Linux tool image.
set -euo pipefail
helper=/repo/hardware/chisel/build-cache-dependencies.sh
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
mkdir "$root/deps"
printf a > "$root/deps/a"
first=$(bash "$helper" "$root/deps")
test "$first" = "$(bash "$helper" "$root/deps")"
printf b > "$root/deps/a"
test "$first" != "$(bash "$helper" "$root/deps")"
printf a > "$root/deps/a"
mv "$root/deps/a" "$root/deps/renamed"
test "$first" != "$(bash "$helper" "$root/deps")"
mv "$root/deps/renamed" "$root/deps/a"
printf a > "$root/deps/b"
test "$first" != "$(bash "$helper" "$root/deps")"
rm "$root/deps/b"
test "$first" = "$(bash "$helper" "$root/deps")"
reject() { if bash "$helper" "$root/deps" >/dev/null 2>&1; then echo 'unexpected dependency acceptance' >&2; exit 1; fi; }
ln -s a "$root/deps/link"; reject; rm "$root/deps/link"
ln "$root/deps/a" "$root/deps/link"; reject; rm "$root/deps/link"
mkfifo "$root/deps/fifo"; reject; rm "$root/deps/fifo"
truncate -s 268435457 "$root/deps/large"; reject; rm "$root/deps/large"
touch "$root/deps/"$'bad\nname'; reject; rm "$root/deps/"$'bad\nname'
printf 'dependency manifest: stable, content, rename, add/remove, links, FIFO, size, names PASS\n'
