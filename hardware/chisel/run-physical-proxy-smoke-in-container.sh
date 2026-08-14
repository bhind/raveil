#!/bin/sh
set -eu

liberty=/home/mambauser/physical-mamba/envs/toolchain/share/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
[ -f "$liberty" ] || {
    echo "error: pinned Sky130 liberty is missing: $liberty" >&2
    exit 1
}

yosys -V | grep -q 'Yosys 0.27'
openroad -version | grep -q '^0264023b6c2a8ae803b8d440478d657387277d93 '
sta -version | grep -q '^2.3.3$'

cat > /tmp/smoke.ys <<EOF
read_verilog -sv /work/physical_proxy_smoke.sv
hierarchy -check -top PhysicalProxySmoke
synth -top PhysicalProxySmoke
dfflibmap -liberty $liberty
abc -liberty $liberty
clean
write_verilog -noattr /tmp/physical_proxy_smoke_netlist.v
stat -liberty $liberty
EOF
yosys -q -l /tmp/yosys.log /tmp/smoke.ys

cat > /tmp/smoke.tcl <<EOF
read_liberty $liberty
read_verilog /tmp/physical_proxy_smoke_netlist.v
link_design PhysicalProxySmoke
read_sdc /work/physical_proxy_smoke.sdc
report_checks -path_delay max -fields {slew cap input_pin} -digits 6
EOF
if ! sta -exit /tmp/smoke.tcl > /tmp/opensta.log 2>&1; then
    cat /tmp/opensta.log >&2
    exit 1
fi

grep -q 'Chip area for module' /tmp/yosys.log
grep -q 'Startpoint:' /tmp/opensta.log

yosys_sha256=$(sha256sum "$(command -v yosys)" | awk '{print $1}')
openroad_sha256=$(sha256sum "$(command -v openroad)" | awk '{print $1}')
opensta_sha256=$(sha256sum "$(command -v sta)" | awk '{print $1}')
liberty_sha256=$(sha256sum "$liberty" | awk '{print $1}')
netlist_sha256=$(sha256sum /tmp/physical_proxy_smoke_netlist.v | awk '{print $1}')
conda_environment_sha256=$(
    micromamba -r /home/mambauser/physical-mamba list -n toolchain --json |
        sha256sum | awk '{print $1}'
)
system_packages_sha256=$(
    dpkg-query -W -f='${Package}=${Version}\n' |
        LC_ALL=C sort | sha256sum | awk '{print $1}'
)
[ "$(dpkg-query -W -f='${Version}' libgl1)" = 1.3.2-1 ]

printf '%s\n' \
    "RAVEIL-PHYSICAL-TOOLCHAIN-V1 status=OK evidence=synthesis-toolchain-commissioning performance=not-measured yosys_version=0.27_4_gb58664d44 openroad_version=2.0_7070_g0264023b6 opensta_version=2.3.3 sky130_version=1.0.457_0_g32e8f23 corner=sky130_fd_sc_hd__tt_025C_1v80 clock_period_ns=20.000 yosys_sha256=$yosys_sha256 openroad_sha256=$openroad_sha256 opensta_sha256=$opensta_sha256 liberty_sha256=$liberty_sha256 conda_environment_sha256=$conda_environment_sha256 system_packages_sha256=$system_packages_sha256 netlist_sha256=$netlist_sha256"
