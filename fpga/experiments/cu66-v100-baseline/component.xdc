# OOC component comparison clock only. This is not a board constraint set.
# External handshakes/memory services have no qualified board latency contract.
# Keep those endpoints visibly unconstrained; do not hide them with false paths.
create_clock -name component_clk -period 10.000 [get_ports clk]
