create_clock -name clock -period 20.000 [get_ports clock]
set_input_delay 1.000 -clock clock [get_ports {reset enable input_word[*]}]
set_output_delay 1.000 -clock clock [get_ports {output_word[*]}]
