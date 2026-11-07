#!/usr/bin/env python3
"""Compare actual SDRAM pin command frequencies from retained campaign logs."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "pin-traffic-results.json"
BASELINE_ALIAS = ROOT / "fpga/experiments/cu66-v91l-scratch-live/results.json"
OVERLAP_ALIAS = ROOT / "fpga/experiments/cu66-v91l-overlap-live/results.json"
BRINGUP_REPORT = ROOT / "fpga/experiments/cu66-v91l-overlap-live/attempts/20261107T033713643539Z-1168179a/results.json"
FINAL_ATTEMPT = ROOT / "fpga/experiments/cu66-v91l-overlap-live/attempts/20261107T034426020935Z-89e4d186/results.json"
PIN_MODEL = ROOT / "fpga/experiments/cu66-v91l-writepipe/sdram_pin_model.sv"
OVERLAP_AUDIT = HERE / "audit.json"

COMMAND_NAMES = {3: "ACTIVATE", 2: "PRECHARGE", 1: "REFRESH", 4: "WRITE", 5: "READ", 0: "MRS"}
COMMAND_ORDER = ("ACTIVATE", "PRECHARGE", "REFRESH", "WRITE", "READ", "MRS")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def natural_mode(report: dict, seed: int = 912901, tac: int = 2) -> dict | None:
    return next((m for m in report.get("modes", [])
                 if m.get("seed") == seed and m.get("t_ac_ns") == tac
                 and not m.get("guard_mode", False)), None)


def final_qualified(report: dict) -> bool:
    natural = {(m.get("seed"), m.get("t_ac_ns")) for m in report.get("modes", [])
               if not m.get("guard_mode", False)}
    expected = {(seed, tac) for seed in (912901, 912902) for tac in (2, 7)}
    guards = [m for m in report.get("modes", []) if m.get("guard_mode", False)]
    return (str(report.get("status", "")).startswith("PASS_EXACT_NATIVE_DECODE_DISPLAY_OVERLAP")
            and len(report.get("modes", [])) == 5 and natural == expected and len(guards) == 1)


def choose_overlap() -> tuple[Path, dict, str, list[tuple[Path, dict, str]]]:
    """Prefer final selected natural mode; retain the known bring-up separately."""
    candidates = []
    alias = load_json(OVERLAP_ALIAS)
    alias_report_path = ROOT / alias["selected_report"]
    alias_report = load_json(alias_report_path)
    if final_qualified(alias_report) and natural_mode(alias_report):
        candidates.append((alias_report_path, alias_report, "final_selected"))
    # The final attempt may have a results.json before the alias is repointed.
    if FINAL_ATTEMPT.exists():
        final_report = load_json(FINAL_ATTEMPT)
        if final_qualified(final_report) and natural_mode(final_report) and all(p != FINAL_ATTEMPT for p, _, _ in candidates):
            candidates.append((FINAL_ATTEMPT, final_report, "final_attempt"))
    if not candidates:
        bringup = load_json(BRINGUP_REPORT)
        if final_qualified(bringup) or not natural_mode(bringup):
            raise AssertionError("expected natural seed 912901/tAC2 bring-up mode")
        candidates.append((BRINGUP_REPORT, bringup, "bringup_fallback_final_pending"))
    primary = candidates[0]
    if OVERLAP_AUDIT.exists() and primary[2] in ("final_selected", "final_attempt"):
        audit = load_json(OVERLAP_AUDIT)
        if audit.get("live_report") is None:
            raise AssertionError("final overlap audit is missing live_report")
        expected_report = ROOT / audit["live_report"]
        if primary[0] != expected_report:
            raise AssertionError("final overlap report differs from audit.live_report")
        if audit.get("live_report_sha256") != sha256(primary[0]):
            raise AssertionError("final overlap report hash differs from audit")
    supporting = []
    if primary[2] != "bringup_fallback_final_pending" and BRINGUP_REPORT.exists():
        br = load_json(BRINGUP_REPORT)
        if natural_mode(br):
            supporting.append((BRINGUP_REPORT, br, "bringup_separate"))
    return (*primary, supporting)


def find_pin_paths(report_path: Path, mode: dict) -> list[Path]:
    base = report_path.parent
    if "pin_logs" in mode:
        paths = [base / name for name in mode["pin_logs"]]
    else:
        paths = [base / f"pins-seed{mode['seed']}-tac{mode['t_ac_ns']}.jsonl.gz"]
    if not paths or any(not p.is_file() for p in paths):
        raise FileNotFoundError(f"missing pin log(s) for {report_path}: {[str(p) for p in paths]}")
    return paths


def scan_pin_logs(paths: list[Path]) -> dict:
    counts = Counter()
    by_bank = {b: Counter() for b in range(4)}
    rows_by_bank: dict[int, Counter] = {b: Counter() for b in range(4)}
    unique_rows: dict[int, set[int]] = {b: set() for b in range(4)}
    active_row: dict[int, int | None] = {b: None for b in range(4)}
    accesses_by_row: dict[int, Counter] = {b: Counter() for b in range(4)}
    active_row_accesses = Counter()
    all_bank_precharges = 0
    records = 0
    last_key = None
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            for line_no, line in enumerate(stream, 1):
                try:
                    event = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"invalid JSON at {path}:{line_no}: {e}") from e
                if event.get("type") != "pin":
                    continue
                code = event.get("command")
                if code not in COMMAND_NAMES:
                    raise ValueError(f"unrecognized SDRAM command {code!r} at {path}:{line_no}")
                bank = int(event["bank"])
                if bank not in by_bank:
                    raise ValueError(f"invalid bank {bank} at {path}:{line_no}")
                name = COMMAND_NAMES[code]
                counts[name] += 1
                by_bank[bank][name] += 1
                records += 1
                key = (int(event["cycle"]), int(event["time_ps"]))
                if last_key is not None and key < last_key:
                    raise ValueError(f"pin records are not monotonic at {path}:{line_no}")
                last_key = key
                if name == "ACTIVATE":
                    row = int(event["address"])
                    rows_by_bank[bank][row] += 1
                    unique_rows[bank].add(row)
                    active_row[bank] = row
                elif name == "PRECHARGE":
                    # A10=1 closes all banks; otherwise only the selected bank.
                    if int(event["address"]) & 0x400:
                        all_bank_precharges += 1
                        for b in active_row:
                            active_row[b] = None
                    else:
                        active_row[bank] = None
                elif name == "REFRESH":
                    for b in active_row:
                        active_row[b] = None
                elif name in ("READ", "WRITE"):
                    row = int(event["row"])
                    if active_row[bank] != row:
                        raise AssertionError(f"{name} not on tracked open row at {path}:{line_no}")
                    accesses_by_row[bank][row] += 1
                    active_row_accesses[name] += 1
    return {
        "pin_records": records,
        "commands": {name: counts[name] for name in COMMAND_ORDER},
        "commands_by_bank": {str(b): {name: by_bank[b][name] for name in COMMAND_ORDER}
                              for b in range(4)},
        "bank_column_semantics": "By-bank counts use raw pin BA fields; an all-bank PRECHARGE (A10=1) is charged to its observed BA field, commonly bank 0, and closes every open row.",
        "all_bank_precharge_count": all_bank_precharges,
        "row_locality_by_bank": {
            str(b): {
                "activate_count": sum(rows_by_bank[b].values()),
                "unique_activated_rows": len(unique_rows[b]),
                "repeated_row_activations": sum(rows_by_bank[b].values()) - len(unique_rows[b]),
                "read_write_column_commands": sum(accesses_by_row[b].values()),
                "rows_with_read_write_commands": len(accesses_by_row[b]),
                "read_write_commands_by_row": {str(row): n for row, n in sorted(accesses_by_row[b].items())},
            } for b in range(4)
        },
        "read_write_commands_on_tracked_open_rows": dict(active_row_accesses),
    }


def campaign(label: str, report_path: Path, report: dict, role: str) -> dict:
    mode = natural_mode(report)
    if mode is None:
        raise AssertionError(f"{label} report does not contain natural seed 912901/tAC2 mode")
    paths = find_pin_paths(report_path, mode)
    return {"label": label, "role": role,
            "report_path": str(report_path.relative_to(ROOT)),
            "report_sha256": sha256(report_path),
            "mode": {"seed": mode["seed"], "t_ac_ns": mode["t_ac_ns"],
                     "guard_mode": mode.get("guard_mode", False), "status": mode.get("status")},
            "pin_log_paths": [str(p.relative_to(ROOT)) for p in paths],
            "pin_log_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in paths},
            "scan": scan_pin_logs(paths)}


def compare(baseline: dict, overlap: dict) -> dict:
    names = list(COMMAND_ORDER)
    base = baseline["scan"]["commands"]
    over = overlap["scan"]["commands"]
    by_bank = {}
    for bank in range(4):
        b = baseline["scan"]["commands_by_bank"][str(bank)]
        o = overlap["scan"]["commands_by_bank"][str(bank)]
        by_bank[str(bank)] = {name: {"baseline": b[name], "overlap": o[name],
                                     "delta": o[name] - b[name]}
                              for name in names}
    deltas = {name: {"baseline": base[name], "overlap": over[name],
                     "delta": over[name] - base[name],
                     "percent": (over[name] - base[name]) * 100.0 / base[name] if base[name] else None}
              for name in names}
    return {"commands": deltas, "commands_by_bank": by_bank,
            "total_commands": {"baseline": sum(base.values()), "overlap": sum(over.values()),
                               "delta": sum(over.values()) - sum(base.values())},
            "ACTIVATE_to_READ_WRITE_ratio": {
                "baseline": base["ACTIVATE"] / (base["READ"] + base["WRITE"]),
                "overlap": over["ACTIVATE"] / (over["READ"] + over["WRITE"]),
            },
            "row_locality_by_bank": {
                str(bank): {
                    "baseline": baseline["scan"]["row_locality_by_bank"][str(bank)],
                    "overlap": overlap["scan"]["row_locality_by_bank"][str(bank)],
                    "delta_ACTIVATE": (overlap["scan"]["row_locality_by_bank"][str(bank)]["activate_count"] -
                                       baseline["scan"]["row_locality_by_bank"][str(bank)]["activate_count"]),
                    "delta_unique_rows": (overlap["scan"]["row_locality_by_bank"][str(bank)]["unique_activated_rows"] -
                                          baseline["scan"]["row_locality_by_bank"][str(bank)]["unique_activated_rows"]),
                    "delta_repeated_row_activations": (overlap["scan"]["row_locality_by_bank"][str(bank)]["repeated_row_activations"] -
                                                       baseline["scan"]["row_locality_by_bank"][str(bank)]["repeated_row_activations"]),
                } for bank in range(4)
            }}


def command_counts(value: dict) -> dict | None:
    """Normalize the independent pin oracle's command-count object when present."""
    if not isinstance(value, dict):
        return None
    names = {name: None for name in COMMAND_ORDER}
    aliases = {"ACTIVATE": "ACTIVATE", "ACT": "ACTIVATE",
               "PRECHARGE": "PRECHARGE", "PRE": "PRECHARGE",
               "REFRESH": "REFRESH", "REF": "REFRESH",
               "WRITE": "WRITE", "WR": "WRITE",
               "READ": "READ", "RD": "READ",
               "MRS": "MRS", "MODEREGISTER": "MRS"}
    for key, count in value.items():
        normalized = str(key).upper().replace("_", "")
        if normalized in aliases and isinstance(count, (int, float)):
            names[aliases[normalized]] = int(count)
        elif str(key) in {str(k) for k in COMMAND_NAMES} and isinstance(count, (int, float)):
            names[COMMAND_NAMES[int(key)]] = int(count)
    if all(v is not None for v in names.values()):
        return names
    return None


def find_actual_pin_oracle(value):
    if isinstance(value, dict):
        # Independent replay currently calls its six categories physical.pin_commands.
        pin_commands = value.get("pin_commands")
        normalized_counts = command_counts(pin_commands) if isinstance(pin_commands, dict) else None
        if normalized_counts is not None:
            return normalized_counts, value
        for key, child in value.items():
            normalized = str(key).lower().replace("_", "")
            if normalized == "actualpinoracle" and isinstance(child, dict):
                for counts_key, raw in child.items():
                    if str(counts_key).lower().replace("_", "") == "commandcounts":
                        normalized_counts = command_counts(raw)
                        if normalized_counts is not None:
                            return normalized_counts, child
            found = find_actual_pin_oracle(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_actual_pin_oracle(child)
            if found is not None:
                return found
    return None


def build() -> dict:
    baseline_alias = load_json(BASELINE_ALIAS)
    baseline_path = ROOT / baseline_alias["selected_report"]
    baseline_report = load_json(baseline_path)
    if not natural_mode(baseline_report):
        raise AssertionError("selected frozen baseline lacks seed 912901/tAC2 mode")
    primary_path, primary_report, primary_role, supporting = choose_overlap()
    baseline = campaign("frozen_scratch_serial_control", baseline_path, baseline_report, "serial_control")
    primary = campaign("native_overlap", primary_path, primary_report, primary_role)
    comparisons = [{"overlap_role": primary_role, "comparison": compare(baseline, primary)}]
    separate_bringup = None
    if supporting:
        p, r, role = supporting[0]
        separate_bringup = campaign("native_overlap_bringup", p, r, role)
        comparisons.append({"overlap_role": role, "comparison": compare(baseline, separate_bringup)})
    primary_comparison = comparisons[0]["comparison"]
    primary_commands = primary_comparison["commands"]
    bank0_rows = primary_comparison["row_locality_by_bank"]["0"]
    observations = [
        f"READ commands changed by {primary_commands['READ']['delta']}; WRITE commands changed by {primary_commands['WRITE']['delta']}.",
        f"ACTIVATE commands changed by {primary_commands['ACTIVATE']['delta']} ({primary_commands['ACTIVATE']['percent']:.2f}%).",
        f"Bank 0 ACTIVATEs changed by {primary_comparison['commands_by_bank']['0']['ACTIVATE']['delta']}; unique activated bank-0 rows changed by {bank0_rows['delta_unique_rows']}; repeated same-row activations changed by {bank0_rows['delta_repeated_row_activations']}.",
        "The extra same-row reactivations are consistent with more frequent row closure/reopening during concurrent access, but pin command counts alone do not prove the cause of decode latency.",
    ]
    pin_sha = sha256(PIN_MODEL)
    # Refresh-script generations may publish this independently replayed pin oracle.
    optional_oracle_crosscheck = None
    oracle_source = None
    mode = natural_mode(primary_report)
    if mode:
        raw_oracle = mode.get("physical", {}).get("pin_oracle_command_counts") or mode.get("pin_oracle_command_counts")
        normalized = command_counts(raw_oracle) if raw_oracle is not None else None
        if normalized is not None:
            optional_oracle_crosscheck = normalized
            oracle_source = "overlap_report"
    if optional_oracle_crosscheck is None and OVERLAP_AUDIT.exists():
        audit = load_json(OVERLAP_AUDIT)
        audited_mode = next((m for m in audit.get("live_modes", [])
                             if m.get("seed") == 912901 and m.get("t_ac_ns") == 2
                             and not m.get("guard_mode", False)), None)
        raw_commands = (audited_mode or {}).get("physical", {}).get("pin_commands")
        normalized_commands = command_counts(raw_commands) if isinstance(raw_commands, dict) else None
        if normalized_commands is not None:
            optional_oracle_crosscheck = normalized_commands
            oracle_source = str(OVERLAP_AUDIT.relative_to(ROOT))
    oracle_check = {"available": optional_oracle_crosscheck is not None}
    if optional_oracle_crosscheck is not None:
        oracle_check.update({"source": oracle_source,
                             "campaign_counts": primary["scan"]["commands"],
                             "oracle_counts": optional_oracle_crosscheck,
                             "equal": optional_oracle_crosscheck == primary["scan"]["commands"]})
        if not oracle_check["equal"]:
            raise AssertionError("streamed pin counts differ from independent PinOracle counts")
    return {
        "schema": "python-gamebub-v91l-overlap-pin-traffic-v1",
        "status": "PASS_ACTUAL_PIN_COMMAND_COUNTS",
        "scope": "observed SDRAM command counts and bank/row locality only; no timing prediction",
        "selection": {"primary_new_mode": primary_role,
                      "final_selected_overlap_natural_mode_available": primary_role in ("final_selected", "final_attempt"),
                      "bringup_retained_separately": separate_bringup is not None},
        "baseline": baseline,
        "primary_overlap": primary,
        "separate_bringup": separate_bringup,
        "comparisons": comparisons,
        "primary_observations": observations,
        "pin_command_encoding": {str(k): v for k, v in COMMAND_NAMES.items()},
        "pin_model_path": str(PIN_MODEL.relative_to(ROOT)),
        "pin_model_sha256": pin_sha,
        "pin_oracle_crosscheck": oracle_check,
        "overlap_audit_sha256": sha256(OVERLAP_AUDIT) if OVERLAP_AUDIT.exists() else None,
        "limitations": [
            "Counts are streamed from actual pin JSONL records, not synthesized from controller transactions.",
            "Command-frequency and row-locality differences alone do not establish the cause of decode contention.",
            "No command counts are converted into latency or controller-cycle predictions.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != rendered:
            raise SystemExit("pin-traffic-results.json differs; rerun without --check")
        print("PASS: deterministic streamed pin-traffic comparison")
    else:
        OUTPUT.write_text(rendered)
        print(rendered, end="")


if __name__ == "__main__":
    main()
