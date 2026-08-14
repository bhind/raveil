#!/bin/sh
set -eu

: "${RAVEIL_PHYSICAL_VARIANT:?variant is required}"
: "${RAVEIL_PHYSICAL_TOP:?top is required}"
: "${RAVEIL_PHYSICAL_BLACKBOX_MODULES:=}"

liberty=/home/mambauser/physical-mamba/envs/toolchain/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
[ -f "$liberty" ]
[ -d /rtl ]
[ -d /evidence ]
[ -z "$(find /evidence -mindepth 1 -print -quit)" ] || {
    echo 'error: evidence directory must be empty' >&2
    exit 1
}

find /rtl -type f \( -name '*.sv' -o -name '*.v' \) -print | LC_ALL=C sort > /tmp/rtl-files
[ -s /tmp/rtl-files ] || {
    echo 'error: no RTL files found' >&2
    exit 1
}

{
    while IFS= read -r file; do
        printf 'read_verilog -sv %s\n' "$file"
    done < /tmp/rtl-files
    printf 'hierarchy -top %s\n' "$RAVEIL_PHYSICAL_TOP"
    old_ifs=$IFS
    IFS=,
    for module in $RAVEIL_PHYSICAL_BLACKBOX_MODULES; do
        if [ -n "$module" ]; then
            printf 'select -assert-count 1 m:%s\n' "$module"
            printf 'blackbox %s\n' "$module"
        fi
    done
    IFS=$old_ifs
    printf 'hierarchy -check -top %s\n' "$RAVEIL_PHYSICAL_TOP"
    printf 'synth -top %s\n' "$RAVEIL_PHYSICAL_TOP"
    printf 'dfflibmap -liberty %s\n' "$liberty"
    printf 'abc -liberty %s\n' "$liberty"
    printf 'clean\n'
    printf 'check -assert\n'
    printf 'write_verilog -noattr /evidence/mapped.v\n'
    printf 'stat -liberty %s\n' "$liberty"
    printf 'tee -o /evidence/stat.json stat -json -liberty %s\n' "$liberty"
} > /tmp/candidate.ys

if ! yosys -q -l /evidence/yosys.log /tmp/candidate.ys; then
    echo 'error: Yosys candidate flow failed' >&2
    exit 1
fi
grep -q "Chip area for module" /evidence/yosys.log

cat > /tmp/candidate.sdc <<EOF
create_clock -name clock -period 20.000 [get_ports clock]
set non_clock_inputs [remove_from_collection [all_inputs] [get_ports clock]]
set_input_delay 1.000 -clock clock $non_clock_inputs
set_output_delay 1.000 -clock clock [all_outputs]
EOF
cat > /tmp/candidate.tcl <<EOF
read_liberty $liberty
read_verilog /evidence/mapped.v
link_design $RAVEIL_PHYSICAL_TOP
read_sdc /tmp/candidate.sdc
report_checks -path_delay max -fields {slew cap input_pin} -digits 6
report_clocks
EOF
if ! sta -exit /tmp/candidate.tcl > /evidence/opensta.log 2>&1; then
    cat /evidence/opensta.log >&2
    exit 1
fi
grep -q 'Startpoint:' /evidence/opensta.log
grep -q 'slack (' /evidence/opensta.log

cp /tmp/rtl-files /evidence/rtl-files.txt
cp /tmp/candidate.ys /evidence/synthesis.ys
cp /tmp/candidate.sdc /evidence/constraint.sdc
cp /tmp/candidate.tcl /evidence/timing.tcl
printf '%s\n' ${RAVEIL_PHYSICAL_BLACKBOX_MODULES:-} | tr ',' '\n' | sed '/^$/d' > /evidence/blackboxes.txt
{
    printf 'yosys_sha256=%s\n' "$(sha256sum "$(command -v yosys)" | awk '{print $1}')"
    printf 'opensta_sha256=%s\n' "$(sha256sum "$(command -v sta)" | awk '{print $1}')"
    printf 'liberty_sha256=%s\n' "$(sha256sum "$liberty" | awk '{print $1}')"
    printf 'yosys_version=%s\n' "$(yosys -V)"
    printf 'opensta_version=%s\n' "$(sta -version)"
    printf 'clock_port=clock\nclock_period_ns=20.000\ninput_delay_ns=1.000\noutput_delay_ns=1.000\n'
} > /evidence/tool-identity.txt
printf '%s\n' \
    "RAVEIL-PHYSICAL-SYNTHESIS-V1 status=OK variant=$RAVEIL_PHYSICAL_VARIANT top=$RAVEIL_PHYSICAL_TOP blackboxes=${RAVEIL_PHYSICAL_BLACKBOX_MODULES:-none} clock_period_ns=20.000 corner=sky130_fd_sc_hd__tt_025C_1v80 evidence=synthesis-estimate performance=candidate-data"
