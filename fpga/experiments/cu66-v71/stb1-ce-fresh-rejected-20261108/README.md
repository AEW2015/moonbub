# CE-factored source: fresh physical implementation rejected

Final setup−0.382ns/TNS−80.561ns at638endpoints; hold+0.031ns, pulse+2.000ns,56,032/56,032routes andzero routingerrors. Positive hold/fullrouting/DRC do not substitute for failed setup. No BIT generated or hardware programmed. V028 remains selected.

The actual routed cone query independently confirms removal of HUD metadata launches to ticket[4]/CE:575startpoints,0HUDgen/ref/fid/bank launches; the explicit metadata-to-CE query has no paths. TargetCE setup+0.289ns/hold+0.787ns,324loads,LUT6driver. Thus the intended local feedback was cut but global parser timing regressed. See actual-cone/REVIEW.md and final full reports. The fresh worstpath is metadata_reference_tag[25] to metadata_plane_bytes[0][9]/CE,15levels including9CARRY4,9.917nsdata,68.276%route.

Exact RTL inputs are V028's79-file source package plus the single source-hashed CE predicate delta preserved in the adjacent proof experiment. No XDC/clock/pin/exception changes were made. Fresh synthesis/resources/CDC/constraints and root approval are preserved. A separately named incremental physical-flow experiment may reuse the passing baseline but must not inherit a timing pass from this failed run or from its functional models.
