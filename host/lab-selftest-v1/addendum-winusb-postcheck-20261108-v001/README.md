# Independent WinUSB binding reconciliation and offline fix addendum

This separate addendum preserves the original failed helper receipt, actual target-bound driver evidence, successful read-only probe, unchanged executed installer bundle, and an offline predicate-only fix/test candidate. It does not rewrite the parent DFU client, any original binding receipt, or the active installer bundle. See reconciliation/RECONCILIATION.json and offline-candidate/README.md for exact scope.

The installed signed-inbox binding is operational on the exact Rev0411 noncomposite DFU node. The executed helper still exited1 due its over-strict post-install DeviceDesc check. Both statements are retained. No automatic reinstall, elevation, reboot or flash action was performed by this addendum. Full backup and any app-only update remain separately owned/gated operations.

Original absolute paths are retained in executed receipts. Restore source/test files into a new C:/moon workspace and run only run-pure-tests.py for predicate replay; it compiles no installer code. Do not execute the preserved installer or treat this candidate as permission to apply a new binding.
