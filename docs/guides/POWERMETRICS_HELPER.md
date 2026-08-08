# Least-privilege powermetrics helper on macOS

This one-time setup permits Raveil to run only its fixed CPU-power and thermal
sampler without an interactive sudo password. Python, the native benchmark,
analysis, sealing, and rclone remain unprivileged.

## Security boundary

The tracked C helper accepts only:

```text
--sample-rate 20..1000 --sample-count 1|-1
```

It rejects every other argument, requires effective UID 0 for sampling, clears
the inherited environment, and directly `execve`s `/usr/bin/powermetrics` with
fixed `cpu_power,thermal`, text format, and buffer settings. It never invokes a
shell. The installed binary and every directory in its absolute path must be
root-owned, non-symlinked, and not group/other writable. Raveil verifies these
properties before invoking sudo.

## One-time installation

From a clean Raveil checkout, compile into a temporary path:

```bash
cc -O2 -std=c11 -Wall -Wextra -Werror \
  tools/powermetrics_helper.c \
  -o /tmp/raveil-powermetrics
/tmp/raveil-powermetrics --version
/usr/bin/shasum -a 256 /tmp/raveil-powermetrics
```

Expected version:

```text
raveil-powermetrics-helper/v1
```

Install the reviewed binary:

```bash
sudo /usr/bin/install -d -o root -g wheel -m 0755 /usr/local/libexec
sudo /usr/bin/install -o root -g wheel -m 0755 \
  /tmp/raveil-powermetrics \
  /usr/local/libexec/raveil-powermetrics
```

Create or edit the sudoers fragment with `visudo`:

```bash
sudo /usr/sbin/visudo -f /private/etc/sudoers.d/raveil-powermetrics
```

Add exactly one line, replacing `ACCOUNT_NAME` with `id -un` output:

```text
ACCOUNT_NAME ALL=(root) NOPASSWD: /usr/local/libexec/raveil-powermetrics
```

The sudoers command intentionally has no arbitrary program or shell. Although
sudo may pass arguments to the helper, the root-owned helper independently
rejects everything outside its fixed allowlist.

Verify configuration and ownership:

```bash
sudo /usr/sbin/visudo -cf /etc/sudoers
/usr/bin/stat -f '%Su:%Sg %Lp %N' /usr/local/libexec/raveil-powermetrics
/usr/local/libexec/raveil-powermetrics --version
/usr/bin/shasum -a 256 /usr/local/libexec/raveil-powermetrics
```

Expected ownership/mode is `root:wheel 755`; the installed hash must equal the
temporary binary hash. If sudoers validation does not include the fragment,
inspect `/private/etc/sudoers` with `sudo visudo` and confirm its include-dir
configuration rather than weakening the rule. Then invalidate any cached sudo
authentication and prove that preflight needs no password:

```bash
sudo -k
python3 -m raveil experiment preflight \
  --manifest benchmarks/manifests/gate1-powermetrics-pilot-v1.json
```

A valid result reports `thermal=Nominal`. `Moderate` or another thermal level
still fails closed. Do not run the whole Raveil CLI as root and do not grant
passwordless access to `/usr/bin/powermetrics`, a shell, Python, or a compiler.
