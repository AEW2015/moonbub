connect -url tcp:localhost:3121
targets -set -filter {name =~ "Hart #0*"}
after 500
set rc [catch {stop} stop_message]
puts "SD_HART_STOP rc=$rc message={$stop_message}"
after 100
set rc [catch {rrd pc} pc]
puts "SD_HART_PC rc=$rc value={$pc}"
set rc [catch {con} con_message]
puts "SD_HART_CONTINUE rc=$rc message={$con_message}"
disconnect
