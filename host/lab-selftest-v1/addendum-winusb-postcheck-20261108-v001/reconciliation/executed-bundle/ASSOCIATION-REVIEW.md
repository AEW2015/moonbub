# Driver-list association blocker and read-only resolution

November8,2026. The frozen helper's global driver-list selection is not yet safe to send toDiInstallDevice with the target device element. This was tested with separate compiled probe programs only; the original helper/source/hash remain unchanged.

## Global list: rejected association

`C:/moon/builds/dfu-driver-association-v001` copied the frozen helper and disabled its persistent branch. It enumerated the global in-memorySPDIT_CLASSDRIVER list from the exact in-boxWinUSBINF, then tried only in-memory/metadata APIs using the selected global driver alongside the actual targetDEVINFO.

- SetupDiGetDriverInfoDetail(target,globalSelected):ERROR_INVALID_PARAMETER87, no detail data.
- SetupDiSetSelectedDriver(target,globalSelected):false/error87.
- SetupDiGetSelectedDriver(target):false/no selected driver.

Thus successful global enumeration alone does not establish the selectedDRIVERis valid for this target context. Do not spend an elevated install attempt using the frozen global-list helper. NoDiInstallDevice call was made.

## Device-associated list: valid association proved without installation

`C:/moon/builds/dfu-driver-association-v002` built a separate probe using device-associated overloads forGet/SetDeviceInstallParams, BuildDriverInfoList(SPDIT_CLASSDRIVER), EnumDriverInfo andGetDriverInfoDetail. The sameDI_ENUMSINGLEINF exactWinUSBINFconstraint and exactMicrosoft/WINUSB/hardware-IDselection remain.

This succeeds on the actual unbound target:

- GetDriverInfoDetail(target,selected):true, exactC:\Windows\INF\winusb.inf, sectionWINUSB.
- SetSelectedDriver(target,selected):true.
- GetSelectedDriver(target):true, providerMicrosoft, descriptionWinUsbDevice.
- GetDriverInfoDetail of the fetched selected driver with target:also true, exactWINUSBsection.

During list building the DEVINFOin-memoryClassGuid becomesUSBDevice`88bae032-5a81-49f0-bc3d-a4ff138216d6`. A separatePnpDevice read afterward still reports the real device as classblank, code28, serviceblank. This is installer context preparation, not a persistent device-class change. Both probe programs hard-disable their persistent install/registry branch.

The actual binding still needs a reviewed elevatedDiInstallDevice call. The read-only association test reduces the specificERROR_INVALID_PARAMETERrisk but does not prove installation or operationalbulkaccess.

## Required helper correction, pending root decision

Change the frozen helper's install-parameter/list/enum/detailP/Invoke signatures from nullable/globaldevice pointers to`ref DEVINFO`. Pass the exacttargetelement throughoutEnumerate/DriverMeta and preserve the samedriverfilters. Obtain the selectedDRIVERfrom that device-associated list. No change toINF, driver package, physicaldeviceproperties or class/service registry is needed.

Recompile and generate a fresh read-only preflight plan because the helper hash changes; the oldv004plan then becomes superseded and must not be used forapply. Repeat the exacttargetnegativecontrol, signaturecheck, before/afterPnPchecks and rootsource review. Keep all privileged branches unexecuted until the intended one-time administrative action is authorized.

Evidence: both directories retain source, compile/execute logs, associationJSONandhashes. The original frozen source hash was independently checked againstbundle-hashes.json and remained identical after both probes. No registry write, install, elevation, reset, firmwarewrite or flashread was performed.

## Root-authorized correction completed

After root's explicit decision, the prior frozen source/executable/wrapper/docs/hash bundle was copied intact to`superseded-global-list-v001`, with`INVALID-FOR-APPLY.json`. The active helper now passes`ref DEVINFO` throughout all driver-list APIs and verifiesSetSelectedDriver/GetSelectedDriver plus target-associated driver details. It uses the fetched associatedDRIVERfor any futureDiInstallDevicecall.

The new64-bithelper compiled and read-only preflightpassed at`C:/moon/dev/evidence/dfu-inbox-bind-preflight-20261108-v005`. The exactMicrosoft/WINUSB/in-boxINFfilters and noncompositeREV0411/code28target guards remain. SeparatePnPreads after this preflight still report code28, no service and no persistent classGUID. An explicit otherMI-child-instance request was again refused before device open. NoApplyflag, elevation, installation or registry write was executed.

The oldv003/v004plan's helper hash now differs and its global-list metadata differs. The active helper's plan gates therefore reject those old plans; use only a new matching target-associated plan after review. Actual Windowsbinding and operationalWinUSBaccess still require the separate authorized elevated step.
