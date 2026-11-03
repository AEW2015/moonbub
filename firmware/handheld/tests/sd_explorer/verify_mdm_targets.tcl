if {[catch {connect -url tcp:localhost:3121} message]} {
    error "Could not connect XSDB to hw_server: $message"
}
after 500
set listing [targets]
puts $listing
if {![regexp {RISC-V at USER2} $listing]} {
    error "MDM target missing: expected 'RISC-V at USER2'"
}
if {![regexp {Hart #0} $listing]} {
    error "MicroBlaze V target missing: expected 'Hart #0'"
}
puts "SD_EXPLORER_MDM_TARGETS_PASS riscv=1 hart0=1"
disconnect
