connect -url tcp:localhost:3121
set harts [targets -target-properties -filter {name =~ "Hart #0*"}]
if {[llength $harts] == 0} {error "Hart #0 not found"}
targets -set -filter {name =~ "Hart #0*"}
catch {con}
after 500
catch {stop}
after 100
puts "SD_MDM_PC value=[rrd pc]"
foreach address {0x42000000 0x42000034 0x42000044 0x42000048 0x4200004c 0x42000050} {
 set rc [catch {mrd -value $address} value]
 puts "SD_MDM_READ address=$address rc=$rc value={$value}"
}
con
disconnect
