# V111 OOC target, loaded BEFORE synthesis; external board interfaces remain unqualified.
create_clock -name component_clk -period 10.000 [get_ports clk]
# No false paths, multicycle paths, clock groups, or guessed I/O delays.
