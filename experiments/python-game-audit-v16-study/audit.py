#!/usr/bin/env python3
"""Read-only v16 study artifact audit. Missing or incomplete evidence stays pending."""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
import importlib.util
import sys
import contextlib
import io
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
AUDIT_PATH = HERE / "audit.json"
STUDIES = {"golden_vectors": "experiments/python-game-golden-vectors-study", "decoder_budget": "experiments/python-game-decoder-budget-study", "refresh_v16": "experiments/python-game-refresh-v16-study", "inline_tag": "experiments/python-game-inline-tag-study", "esp32_gateway": "experiments/python-game-esp32-gateway-study"}
READY_STUDIES = {"golden_vectors", "decoder_budget", "refresh_v16", "inline_tag", "esp32_gateway"}
TARGET = {"canvas": [720, 480], "active_image": [720, 405], "fps": 30}
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024), b""): h.update(block)
    return h.hexdigest()
def portable(path):
    try: return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError: return "external:"+path.name
def resolve_pin(raw):
    p=Path(raw); marker="/moonbub-30fps-study/"
    if marker in raw: return ROOT/Path(raw.split(marker,1)[1])
    return p if p.is_absolute() else ROOT/p
def test_log(path):
    if not path.is_file(): return {"status":"missing","passed_count":None}
    text=path.read_text(errors="replace"); m=re.search(r"Ran (\d+) tests?",text)
    ok=m is not None and "OK" in text and "FAILED (" not in text and "ERROR" not in text
    return {"status":"pass" if ok else "invalid","passed_count":int(m.group(1)) if m else None}

def load_module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

def audit_golden(data, directory):
    errors=[]; counts=data.get("counts",{}); cohorts=data.get("cohorts",[])
    rows=[row for c in cohorts for row in c.get("rows",[])]
    blobs=[]
    def add_descriptor(item):
        if isinstance(item,dict):
            if "path" in item and "stored_sha256" in item: blobs.append(item)
            else:
                for child in item.values(): add_descriptor(child)
        elif isinstance(item,list):
            for child in item: add_descriptor(child)
    add_descriptor(cohorts); negatives=data.get("negative_vectors",[]); add_descriptor(negatives)
    unique={}
    for desc in blobs:
        if not desc: errors.append("missing blob descriptor"); continue
        rel=Path(desc.get("path","")); p=directory/rel
        if rel.is_absolute() or ".." in rel.parts:
            errors.append(f"unsafe blob path: {rel}"); continue
        if not p.is_file(): errors.append(f"missing blob: {rel}"); continue
        raw=p.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
        unique[rel.as_posix()]={"stored_sha256":digest,"expected":desc.get("stored_sha256"),"matches":digest==desc.get("stored_sha256")}
        if digest!=desc.get("stored_sha256"): errors.append(f"stored blob hash mismatch: {rel}")
    actual_formats=set(); selected_words=0
    for row in rows:
        ident=row.get("identity",{}); actual_formats.add(ident.get("inner_codec")); selected_words+=row.get("selected_pixels",0)
        packet=ident.get("packet_bytes")
        if packet!=row.get("ar02",{}).get("raw_bytes"): errors.append("AR02 packet byte count mismatch")
    neg_targets={"receiver":0,"feedback":0}; atomic_expected=True
    for item in negatives:
        target=item.get("target","")
        neg_targets["receiver" if target=="receiver.begin" else "feedback" if target=="encoder.ack" else "unknown"]=neg_targets.get("receiver" if target=="receiver.begin" else "feedback" if target=="encoder.ack" else "unknown",0)+1
        atomic_expected &= "unchanged" in item.get("expected","")
    replay={"status":"not_run"}
    verifier=directory/"verify.py"
    try:
        sys.path.insert(0,str(directory))
        mod=load_module(verifier,"v16_golden_verify")
        replay={"status":"pass","counts":mod.verify()}
    except Exception as exc:
        errors.append(f"golden vector replay failed: {type(exc).__name__}: {exc}"); replay={"status":"fail","error":str(exc)}
    if data.get("schema")!="gamebub-ar02-golden-v1" or data.get("epoch")!=16: errors.append("golden schema/epoch mismatch")
    if counts!={"cohorts":3,"positive_frames":10,"negative_vectors":10,"gf02_datagrams":12,"selected_ui_words":768}: errors.append(f"golden counts mismatch: {counts}")
    object_files=list((directory/"objects").glob("*"))
    object_bytes=sum(p.stat().st_size for p in object_files if p.is_file())
    if len(cohorts)!=3 or len(rows)!=10 or len(negatives)!=10 or len(unique)!=84: errors.append("golden manifest row/object totals mismatch")
    if len(object_files)!=84 or object_bytes!=89759: errors.append(f"object store count/size mismatch: {len(object_files)}/{object_bytes}")
    if actual_formats!={"GM01","SR01"} or selected_words!=768: errors.append("golden packet formats or selected UI words mismatch")
    if neg_targets!={"receiver":8,"feedback":2} or not atomic_expected: errors.append("negative vector targets/atomicity expectations mismatch")
    return {"status":"verified" if not errors else "invalid","schema":data.get("schema"),"epoch":data.get("epoch"),"source_pin_count":len(data.get("source_sha256",{})),"cohort_count":len(cohorts),"positive_frames":len(rows),"negative_vectors":len(negatives),"gf02_datagrams":sum(len(r.get("gf02",[])) for r in rows),"selected_ui_words":selected_words,"inner_formats":sorted(x for x in actual_formats if x),"negative_targets":neg_targets,"negative_atomicity_expected":atomic_expected,"unique_object_count":len(unique),"object_store_bytes":object_bytes,"objects":unique,"replay":replay,"errors":errors}

def audit_budget(data, directory):
    errors=[]; traces=data.get("traces",[]); estimates=data.get("estimates",[])
    actual=[t for t in traces if t.get("packet_sha256")]; synthetic=[t for t in traces if not t.get("packet_sha256")]
    bounded=sum(1 for t in actual if isinstance(t.get("packet_bytes"),int) and t["packet_bytes"]<=49152)
    all_no_hardware=all(not x.get("estimate",{}).get("hardware_fit_proven",True) and not x.get("estimate",{}).get("line_deadline_proven",True) for x in estimates)
    scope=data.get("scope","")+" "+data.get("architecture_scope","")+" "+data.get("entropy_scope","")+" "+data.get("memory_scope","")+" "+data.get("nominal_timing_scope","")
    conditional=("neither synthesis" in scope.lower() or "not synthesis" in scope.lower()) and all(word in scope.lower() for word in ("not a peak physical","not board service","hypothetical"))
    clock_sweep=data.get("clock_sweep",[])
    if len(traces)!=19 or len(actual)!=18 or len(synthetic)!=1 or len(estimates)!=57 or len(clock_sweep)!=52: errors.append("decoder trace/budget/sweep counts differ from 18 actual + 1 analytical, 57 budgets, and 52 clock points")
    if bounded!=len(actual): errors.append("actual packet trace exceeds complete frame cap")
    if data.get("capacity_total")!=sum(data.get("capacity_bytes",{}).values()): errors.append("capacity total does not match category sum")
    if not all_no_hardware: errors.append("cycle model marked hardware fit or line deadline proven")
    if not conditional: errors.append("cycle-model scope does not state implementation/timing assumptions")
    if any("Only average serialized" not in x.get("caveat","") for x in clock_sweep): errors.append("clock sweep lacks its average-only/no-closure caveat")
    media=data.get("input_media",{}); media_path=Path(media.get("source","")); media_hash=sha256(media_path) if media_path.is_file() else None
    media_ok=media_hash==media.get("source_sha256")
    if not media_ok: errors.append("offline native source media missing or hash mismatch")
    replay={"status":"not_run"}
    try:
        sys.path.insert(0,str(directory)); mod=load_module(directory/"verify.py","v16_budget_verify")
        with contextlib.redirect_stdout(io.StringIO()): mod.main()
        replay={"status":"pass"}
    except Exception as exc:
        errors.append(f"budget arithmetic replay failed: {type(exc).__name__}: {exc}"); replay={"status":"fail","error":str(exc)}
    return {"status":"verified" if not errors else "invalid","trace_count":len(traces),"actual_packet_traces":len(actual),"analytical_traces":len(synthetic),"estimate_count":len(estimates),"clock_sweep_points":len(clock_sweep),"source_pin_count":len(data.get("source_sha256",{})),"actual_packets_within_cap":bounded,"capacity_bytes":data.get("capacity_bytes"),"capacity_total":data.get("capacity_total"),"modeled_memory_capacity_bytes":data.get("modeled_memory_capacity_bytes"),"advertised_sdram_bytes":data.get("advertised_sdram_bytes"),"advertised_sram_bytes":data.get("advertised_sram_bytes"),"all_line_deadlines_unproven":all_no_hardware,"assumptions_explicit":conditional,"input_media":{"path":portable(media_path),"expected_sha256":media.get("source_sha256"),"actual_sha256":media_hash,"matches":media_ok},"verification_replay":replay,"scopes":{k:data.get(k) for k in ("scope","architecture_scope","entropy_scope","memory_scope","nominal_timing_scope")},"errors":errors}

def audit_refresh(data, directory):
    errors=[]; cases=data.get("cases",[]); summary=data.get("summary",[])
    profiles={c.get("profile"):c for c in cases}; sums={x.get("profile"):x for x in summary}
    names=["gm_initial_only","gm_refresh30","gm_refresh30_repeat","gm_refresh30_coarse","gm_refresh60_coarse","gm_refresh90_coarse"]
    case_rows=[]; all_ui=True; all_same_manifest=True; all_drained=True; all_packet_caps=True; strict_steady=[]
    first=cases[0].get("manifest") if cases else None
    for c in cases:
        name=c.get("profile"); r=c.get("result",{}); manifest=c.get("manifest",{}); commits=r.get("commits",[])
        all_same_manifest &= manifest==first
        all_ui &= bool(commits) and all(x.get("selected_exact_pixels")==21120 and x.get("selected_ui_mismatches")==0 for x in commits) and r.get("config",{}).get("exact_ui") is True
        all_drained &= not any(r.get(k) for k in ("unresolved_ids","unresolved_encoder_pending","unresolved_ingress","unresolved_receiver_readers","unresolved_decode")) and all(x is None for x in r.get("unresolved_sender_slots",[]))
        all_packet_caps &= all(p.get("bytes",49153)<=r.get("config",{}).get("frame_cap",0) for p in r.get("packets",[]) if p.get("admitted"))
        hist={p.get("id"):p for p in commits}; presented=[p for p in r.get("presented",[]) if 500<=p.get("at_ms",-1)<5500]
        ids=[p.get("id") for p in presented]; input_hashes=[manifest.get("frame_sha256",[])[i] for i in ids]
        output_hashes=[hist[i].get("rgb_sha256") for i in ids if i in hist]
        distinct=len(set(ids))==len(set(input_hashes))==len(set(output_hashes))==len(ids)
        steady_rate=len(ids)/5
        strict_steady.append({"profile":name,"strict":r.get("presented_strict"),"eventual":r.get("presented_eventual"),"steady_window_unique_images":len(ids),"modeled_steady_ids_per_second":steady_rate,"unique_input_and_decoded_hashes":distinct})
        if not distinct: errors.append(f"{name}: steady-window presentation hashes are not unique")
        if r.get("capture_count")!=180 or len(manifest.get("frame_sha256",[]))!=180: errors.append(f"{name}: expected 180 input IDs")
        case_rows.append({"profile":name,"refresh_period":r.get("config",{}).get("refresh_period"),"refresh_background_scale":r.get("config",{}).get("refresh_key_background_scale"),"capture_count":r.get("capture_count"),"strict":r.get("presented_strict"),"eventual":r.get("presented_eventual"),"decoded_commits":len(commits),"selected_ui_words_per_commit":sorted(set(x.get("selected_exact_pixels") for x in commits)),"selected_ui_mismatch_rows":sum(x.get("selected_ui_mismatches",1)!=0 for x in commits),"steady_unique_images":len(ids),"steady_ids_per_second":steady_rate,"reference_publications":len(r.get("publications",[])),"all_drained":not bool(r.get("unresolved_ids") or r.get("unresolved_encoder_pending") or r.get("unresolved_ingress") or r.get("unresolved_receiver_readers") or r.get("unresolved_decode"))})
    if data.get("case_count")!=6 or len(cases)!=6 or set(profiles)!=set(names) or set(sums)!=set(names): errors.append("refresh six-case profile set mismatch")
    if not all_same_manifest or not first or first.get("unique_frame_count")!=180 or first.get("frame_count")!=180: errors.append("refresh cases do not share the same 180-frame source manifest")
    if not all_ui: errors.append("refresh full UI exact-word coverage failed")
    if not all_drained: errors.append("refresh run did not fully drain all modeled resources")
    if not all_packet_caps: errors.append("refresh admitted packet exceeds frame cap")
    media=first or {}; media_path=Path(media.get("source","")); media_hash=sha256(media_path) if media_path.is_file() else None
    media_ok=bool(media_hash and media_hash==media.get("source_sha256"))
    if not media_ok: errors.append("refresh native input media missing or hash mismatch")
    # Check profile-level actual strict counts and bounded steady-window rates.
    expected={"gm_initial_only":(174,177,149,29.8),"gm_refresh30":(158,160,133,26.6),"gm_refresh30_repeat":(160,162,134,26.8),"gm_refresh30_coarse":(161,163,135,27.0),"gm_refresh60_coarse":(168,171,144,28.8),"gm_refresh90_coarse":(172,174,146,29.2)}
    for row in strict_steady:
        target=expected.get(row["profile"])
        if not target or (row["strict"],row["eventual"],row["steady_window_unique_images"])!=target[:3] or abs(row["modeled_steady_ids_per_second"]-target[3])>1e-9: errors.append(f"refresh presentation counts differ for {row['profile']}")
    analysis_path=directory/"analyze.py"; matched_path=directory/"matched-refresh.json"
    binding={"status":"missing"}; comparison={}
    try:
        matched=json.loads(matched_path.read_text()); result_hash=sha256(directory/"results.json"); analyzer_hash=sha256(analysis_path)
        sys.path.insert(0,str(directory)); analyzer=load_module(analysis_path,"v16_refresh_analyzer"); rebuilt=analyzer.build()
        binding_ok=(matched==rebuilt and matched.get("results_sha256")==result_hash and matched.get("analyzer_sha256")==analyzer_hash)
        if not binding_ok: errors.append("matched-refresh analysis does not bind to frozen result and analyzer")
        pairs=matched.get("matched_independent_key_pairs",[]); ids=[x.get("id") for x in pairs]
        comparison={"matched_key_ids":ids,"matched_key_count":len(pairs),"regular_key_bytes":matched.get("matched_key_total_regular_bytes"),"coarse_key_bytes":matched.get("matched_key_total_coarse_bytes"),"complete_body_saving_percent":matched.get("matched_key_complete_body_saving_percent"),"common_decoded_ids":len(matched.get("regular_and_coarse_common_decoded_ids",[])),"common_decoded_source_rgb565_mse_delta":matched.get("common_decoded_source_rgb565_mse_delta"),"claim_limit":matched.get("limit")}
        if ids!=[31,62,93,124,155] or (comparison["regular_key_bytes"],comparison["coarse_key_bytes"])!=(152754,128210) or abs(comparison["complete_body_saving_percent"]-16.0676643492)>1e-8 or abs(comparison["common_decoded_source_rgb565_mse_delta"]-0.37191718107)>1e-8: errors.append("matched refresh-key bytes/quality comparison mismatch")
        binding={"status":"verified" if binding_ok else "invalid","results_sha256_matches":matched.get("results_sha256")==result_hash,"analyzer_sha256_matches":matched.get("analyzer_sha256")==analyzer_hash}
    except Exception as exc:
        errors.append(f"matched refresh analysis check failed: {type(exc).__name__}: {exc}"); binding={"status":"invalid","error":str(exc)}
    replay={"status":"not_run"}
    try:
        sys.path.insert(0,str(directory)); verify=load_module(directory/"verify.py","v16_refresh_verify")
        with contextlib.redirect_stdout(io.StringIO()): verify.main()
        replay={"status":"pass"}
    except Exception as exc:
        errors.append(f"refresh retained-evidence replay failed: {type(exc).__name__}: {exc}"); replay={"status":"fail","error":str(exc)}
    scope=data.get("scope","").lower()
    if "no capture" not in scope or not any(x in scope for x in ("no hardware","no physical","not hardware","hardwareproof")): errors.append("refresh scope does not disclaim physical capture/hardware claims")
    return {"status":"verified" if not errors else "invalid","case_count":len(cases),"source_pin_count":len(data.get("source_sha256",{})),"input_media":{"path":portable(media_path),"expected_sha256":media.get("source_sha256"),"actual_sha256":media_hash,"matches":media_ok},"input_frame_count":first.get("frame_count") if first else None,"input_hashes_unique":first.get("unique_frame_count") if first else None,"all_cases_same_manifest":all_same_manifest,"all_ui_21120_exact":all_ui,"all_selected_ui_mismatches":0 if all_ui else None,"all_model_runs_drained":all_drained,"all_admitted_packets_within_cap":all_packet_caps,"profile_summaries":case_rows,"strict_vs_steady":strict_steady,"matched_refresh_keys":comparison,"analysis_binding":binding,"verification_replay":replay,"quality_scope":data.get("quality_scope"),"policy_scope":data.get("policy_scope"),"evidence_scope":data.get("scope"),"errors":errors}

def audit_inline_tag(data, directory):
    errors=[]; cases=data.get("cases",[]); full=[c for c in cases if (c.get("width"),c.get("height"))==(720,480)]
    exact_tags=sum(c.get("tag")==c.get("reference_tag") for c in cases)
    strata={}
    for c in cases: strata[c.get("scope")]=strata.get(c.get("scope"),0)+1
    full_storage=all(c.get("peak_stripe_storage_bytes")==11520 for c in full)
    full_sha=all(c.get("canonical_bytes_hashed")==1036804 for c in full)
    full_reread=all(c.get("conditional_eliminable_packed8_publication_reread_bytes")==518400 for c in full)
    counter=data.get("counterfactual",[]); expected={"conservative":(None,None),"nominal":(69.7240202230,60.6905629740),"optimistic":(37.2274470090,33.8151247341)}
    counter_rows=[]
    for x in counter:
        before,after=expected.get(x.get("scenario"),(float("nan"),float("nan")))
        correct=(x.get("baseline_planning_ms")==before and x.get("conditional_planning_ms")==after) if before is None else (abs(x.get("baseline_planning_ms",0)-before)<1e-8 and abs(x.get("conditional_planning_ms",0)-after)<1e-8)
        if not correct: errors.append(f"inline tag counterfactual mismatch: {x.get('scenario')}")
        counter_rows.append({k:x.get(k) for k in ("scenario","baseline_planning_ms","conditional_planning_ms","eliminated_packed8_reread_bytes","canonical_sha_input_bytes_unchanged","sha_stage_cycles_unchanged","scope")})
    limits=data.get("limits","").lower()
    conditional_only=("already decoded whole planes" in limits and "no actual decoderfusion" in limits and "full-frame memory reread saved" in limits and all("No fused decoder" in x.get("scope","") for x in counter))
    expected_strata={"retained synthetic golden decode":10,"retained native-derived actual AR02 decode; three related source IDs per mode":6,"deterministic synthetic canonical YUV, not encoded gameplay":4}
    if data.get("case_count")!=20 or len(cases)!=20 or len(full)!=8 or strata!=expected_strata: errors.append("inline-tag case totals/cohorts differ from the frozen study")
    if exact_tags!=20 or not full_storage or not full_sha or not full_reread: errors.append("canonical tags or full-frame stripe/SHA/reread byte counts mismatch")
    if not conditional_only: errors.append("inline-tag result overstates decoder fusion or read removal")
    replay={"status":"not_run"}
    try:
        sys.path.insert(0,str(directory)); verify=load_module(directory/"verify.py","v16_inline_verify"); replay={"status":"pass","summary":verify.verify()}
    except Exception as exc:
        errors.append(f"inline-tag retained evidence replay failed: {type(exc).__name__}: {exc}"); replay={"status":"fail","error":str(exc)}
    return {"status":"verified" if not errors else "invalid","case_count":len(cases),"cohort_counts":strata,"full720x480_cases":len(full),"source_pin_count":len(data.get("source_sha256",{})),"all_canonical_tags_match":exact_tags==20,"full_resolution_stripe_storage_bytes":11520 if full_storage else None,"canonical_full_frame_sha_bytes":1036804 if full_sha else None,"conditional_packed8_publication_reread_bytes":518400 if full_reread else None,"decoder_fusion_proven":False,"conditional_budget_only":conditional_only,"counterfactual":counter_rows,"verification_replay":replay,"limits":data.get("limits"),"errors":errors}

def audit_gateway(data, directory):
    errors=[]; workloads=data.get("workloads",[]); scenarios=data.get("scenarios",[]); links=data.get("link_burst_sweep",[]); ram=data.get("ram_scenarios",[])
    work={w.get("profile"):w for w in workloads}; names=["gm_initial_only","gm_refresh30","gm_refresh30_coarse","cap_stress_60"]
    workload_counts={k:len(v.get("frames",[])) for k,v in work.items()}
    rows=[]; all_bounded=True; all_drain=True; no_qual_claim=True; bykey={}
    for row in scenarios:
        r=row.get("result",{}); c=r.get("config",{}); key=(row.get("workload"),c.get("name")); bykey[key]=r
        all_bounded &= r.get("peak_mailbox",99)<=6 and r.get("peak_dma_working_packets",99)<=1
        all_drain &= r.get("queue_drained") is True
        no_qual_claim &= r.get("protocol_supported_by_current_firmware") is False and r.get("physical_30fps_proven") is False
        rows.append({"workload":key[0],"scenario":key[1],"frames":r.get("frames"),"strict_completed":r.get("strict_completed_frames"),"eventual_completed":r.get("completed_frames"),"mailbox_drops":r.get("counters",{}).get("mailbox_full",0),"peak_mailbox":r.get("peak_mailbox"),"max_age_ms":r.get("maximum_completed_age_ms"),"drain_end_ms":r.get("drain_end_ms"),"transport_queue_drained":r.get("transport_queue_drained"),"active_incomplete_frame_at_end":r.get("active_incomplete_frame_at_end"),"idle_500ms_timeout_simulated":r.get("idle_500ms_timeout_simulated"),"protocol_supported":r.get("protocol_supported_by_current_firmware"),"physical_30fps_proven":r.get("physical_30fps_proven")})
    facts=data.get("facts",{})
    expected_facts={"cpu_hz":240000000,"external_psram_enabled":False,"payload_format":"MSV1 JPEG only","ar02_gf02_implemented":False,"payload_bytes":1024,"header_bytes":40,"dma_buffer_bytes":1065,"main_stack_bytes":20480,"stream_stack_bytes":16384,"udp_mailbox_packets":6,"wifi_static_rx":10,"wifi_dynamic_rx":32,"crc_bit_steps_per_payload_byte":8,"qspi_write_clock_cap_hz":40000000,"qspi_read_clock_cap_hz":16000000,"device_lock_policy":"try_lock_and_drop_frame","abort_retry_bound_ms":100,"abort_retry_sleep_ms":1}
    facts_match=all(facts.get(k)==v for k,v in expected_facts.items())
    if not facts_match: errors.append("source-extracted firmware facts differ from expected constraints")
    if len(workloads)!=4 or set(work)!=set(names) or workload_counts!={"gm_initial_only":177,"gm_refresh30":160,"gm_refresh30_coarse":163,"cap_stress_60":60}: errors.append("gateway workload/count mismatch")
    if len(scenarios)!=32 or len(bykey)!=32 or any(sum(1 for k in bykey if k[0]==n)!=8 for n in names): errors.append("gateway principal case count/profile coverage mismatch")
    if len(links)!=20 or len(ram)!=3 or len(data.get("source_sha256",{}))!=13: errors.append("gateway link/RAM/source-pin evidence count mismatch")
    if not all_bounded or not all_drain or not no_qual_claim: errors.append("gateway queue bound/drain or hardware/protocol qualification guard failed")
    if any(r.get("idle_500ms_timeout_simulated") is not False for r in (x["result"] for x in scenarios)): errors.append("gateway 500 ms idle timeout was incorrectly treated as modeled")
    nominal=bykey.get(("gm_initial_only","nominal"),{}); burst=bykey.get(("gm_initial_only","nominal_burst8"),{}); lock=bykey.get(("gm_initial_only","nominal_lock_busy"),{}); abort=bykey.get(("gm_initial_only","lock_busy_abort100ms"),{}); cap=bykey.get(("cap_stress_60","nominal"),{})
    checks={"nominal_initial":(nominal.get("strict_completed_frames"),nominal.get("completed_frames"),nominal.get("frames"),nominal.get("maximum_completed_age_ms"),nominal.get("mean_input_payload_mbps"),nominal.get("required_ipv4_udp_mbps")),
            "burst8":(burst.get("strict_completed_frames"),burst.get("completed_frames"),burst.get("counters",{}).get("mailbox_full")),
            "lock_busy":(lock.get("strict_completed_frames"),lock.get("completed_frames"),lock.get("counters",{}).get("mailbox_full",0)),
            "abort100":(abort.get("strict_completed_frames"),abort.get("completed_frames"),abort.get("counters",{}).get("mailbox_full")),
            "cap_stress":(cap.get("strict_completed_frames"),cap.get("completed_frames"),cap.get("frames"),cap.get("required_ipv4_udp_mbps"),cap.get("drain_end_ms"),cap.get("maximum_completed_age_ms"))}
    expected={"nominal_initial":(176,177,177,43.5470222222,5.6369706667,6.019856),"burst8":(0,0,460),"lock_busy":(156,157,0),"abort100":(97,98,1484),"cap_stress":(38,60,60,12.57984,3145.5114778,1178.8448111)}
    for key, exp in expected.items():
        act=checks[key]
        equal=(len(act)==len(exp) and all(abs(a-b)<1e-7 if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)) else a==b for a,b in zip(act,exp)))
        if not equal: errors.append(f"gateway retained summary mismatch: {key}")
    ram_summaries=[(x.get("assumed_available_internal_bytes"),x.get("total_reserve"),x.get("reserve_margin"),x.get("fit_proven"),x.get("psram_assumed")) for x in ram]
    if [x[2] for x in ram_summaries]!=[-13401,52135,117671] or any(x[3] is not False or x[4] is not False for x in ram_summaries): errors.append("gateway RAM margins or fit/PSRAM caveats mismatch")
    replay={"status":"not_run"}
    try:
        sys.path.insert(0,str(directory)); verify=load_module(directory/"verify.py","v16_gateway_verify")
        with contextlib.redirect_stdout(io.StringIO()): verify.main()
        replay={"status":"pass"}
    except Exception as exc:
        errors.append(f"gateway source/scenario replay failed: {type(exc).__name__}: {exc}"); replay={"status":"fail","error":str(exc)}
    lock_paths={"status":"not_run"}
    try:
        from dataclasses import replace
        sys.path.insert(0,str(directory)); gw=load_module(directory/"gateway.py","v16_gateway_model")
        fresh=gw.simulate([dict(id=0,bytes=1024)],replace(gw.Config(),lock_busy_ms=16.6666667))
        frames=[dict(id=i,bytes=16000) for i in range(10)]; cfg=replace(gw.Config(),lock_period_ms=1000,lock_busy_ms=1,lock_phase_ms=3.5)
        mid_default=gw.simulate(frames,cfg); mid_abort=gw.simulate(frames,replace(cfg,abort_recovery_ms=100))
        fresh_ok=(fresh["counters"].get("begin_device_lock_busy")==1 and fresh["counters"].get("abort_calls",0)==0 and fresh["abort_service_us"]==0)
        mid_ok=(mid_default["counters"].get("device_lock_busy",0)>0 and mid_abort["abort_service_us"]>mid_default["abort_service_us"] and mid_abort["counters"].get("mailbox_full",0)>mid_default["counters"].get("mailbox_full",0))
        if not fresh_ok or not mid_ok: errors.append("fresh-begin/mid-frame lock failure accounting regression")
        lock_paths={"status":"verified" if fresh_ok and mid_ok else "invalid","fresh_begin":{"begin_lock_busy":fresh["counters"].get("begin_device_lock_busy"),"abort_calls":fresh["counters"].get("abort_calls",0),"abort_service_us":fresh["abort_service_us"]},"midframe_forward_failure":{"device_lock_busy":mid_abort["counters"].get("device_lock_busy"),"abort_service_default_us":mid_default["abort_service_us"],"abort_service_100ms_us":mid_abort["abort_service_us"],"default_mailbox_drops":mid_default["counters"].get("mailbox_full",0),"abort100_mailbox_drops":mid_abort["counters"].get("mailbox_full",0)}}
    except Exception as exc:
        errors.append(f"gateway lock-path replay failed: {type(exc).__name__}: {exc}"); lock_paths={"status":"fail","error":str(exc)}
    return {"status":"verified" if not errors else "invalid","principal_case_count":len(scenarios),"workload_count":len(workloads),"workload_frame_counts":workload_counts,"link_burst_cases":len(links),"ram_scenarios":ram_summaries,"source_pin_count":len(data.get("source_sha256",{})),"source_facts_match":facts_match,"source_facts":{k:facts.get(k) for k in expected_facts},"bounded_mailbox_and_dma":all_bounded,"scenario_queues_drained":all_drain,"protocol_and_hardware_claims_false":no_qual_claim,"unmodeled_idle_timeout_explicit":all(x["result"].get("idle_500ms_timeout_simulated") is False for x in scenarios),"transport_drain_separate_from_active_frame":all("active_incomplete_frame_at_end" in x["result"] and "transport_queue_drained" in x["result"] for x in scenarios),"key_scenario_summaries":checks,"corrected_lock_failure_paths":lock_paths,"verification_replay":replay,"note":data.get("note"),"limits":data.get("limits"),"errors":errors}
def audit_study(key, rel_dir):
    directory=ROOT/rel_dir; result_path=directory/"results.json"
    out={"status":"pending","path":rel_dir,"artifacts":{},"source_pins":[],"errors":[]}
    if key not in READY_STUDIES:
        out["errors"].append("awaiting final evidence signal")
        return out
    out["test_log"]=test_log(directory/"tests.log")
    if not directory.is_dir(): out["errors"].append("study directory missing"); return out
    for name in ("README.md","SCHEMA.md","results.json","tests.log","verify.log","analysis-verify.log"):
        p=directory/name; out["artifacts"][name]={"present":p.is_file(),"sha256":sha256(p) if p.is_file() else None}
    if not result_path.is_file(): out["errors"].append("results.json missing"); return out
    try: data=json.loads(result_path.read_text())
    except (OSError,json.JSONDecodeError) as exc:
        out["status"]="invalid"; out["errors"].append(f"results.json unreadable: {exc}"); return out
    out["schema"]={"top_level_type":type(data).__name__,"top_level_keys":sorted(data) if isinstance(data,dict) else []}
    out["result_sha256"]=sha256(result_path)
    pins=data.get("source_sha256",{}) if isinstance(data,dict) else {}
    for raw, expected in pins.items():
        p=resolve_pin(raw); actual=sha256(p) if p.is_file() else None
        entry={"path":portable(p),"expected":expected,"actual":actual,"matches":actual==expected}; out["source_pins"].append(entry)
        if not entry["matches"]: out["errors"].append(f"source hash pin missing or mismatched: {entry['path']}")
    out["result_summary"]={k:data.get(k) for k in ("study","evidence","case_count","frame_count","event_count","status") if isinstance(data,dict) and k in data}
    if key=="golden_vectors": out["analysis"]=audit_golden(data,directory)
    if key=="decoder_budget": out["analysis"]=audit_budget(data,directory)
    if key=="refresh_v16": out["analysis"]=audit_refresh(data,directory)
    if key=="inline_tag": out["analysis"]=audit_inline_tag(data,directory)
    if key=="esp32_gateway": out["analysis"]=audit_gateway(data,directory)
    if out.get("analysis",{}).get("status")=="invalid": out["errors"].extend(out["analysis"].get("errors",[]))
    if out["test_log"]["status"]!="pass": out["errors"].append("study test log missing or not a passing unittest log")
    out["status"]=("verified" if key in READY_STUDIES and not out["errors"] and out.get("analysis",{}).get("status")=="verified"
                   else "pending" if not out["errors"] else "invalid")
    return out
def load_audit():
    data=json.loads(AUDIT_PATH.read_text()); results={k:audit_study(k,v) for k,v in STUDIES.items()}; data["results"]=results
    for key,result in results.items(): data["inputs"][key]["status"]=result["status"]
    data["status"]="verified" if all(x["status"]=="verified" for x in results.values()) else ("invalid" if any(x["status"]=="invalid" for x in results.values()) else "pending")
    golden=results["golden_vectors"]
    data["checks"]["golden_vector_schema_counts_hashes_and_negative_atomicity"]=golden["status"]
    data["checks"]["packet_vector_selected_words"]=golden["status"]
    data["checks"]["decoder_cyclemodel_assumptions_vs_hardware"]=results["decoder_budget"]["status"]
    data["checks"]["refresh_source_hashes_and_full_ui_coverage"]=results["refresh_v16"]["status"]
    data["checks"]["strict_vs_steady_fps_and_reference_publication"]=results["refresh_v16"]["status"]
    data["checks"]["inline_canonical_tag_order_and_conditional_read_reread"]=results["inline_tag"]["status"]
    data["checks"]["gateway_firmware_evidence_vs_cyclemodel"]=results["esp32_gateway"]["status"]
    return data
def main():
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("--check",action="store_true",help="recompute and compare without writing audit.json")
    args=parser.parse_args(); data=load_audit(); rendered=json.dumps(data,indent=2,sort_keys=True)+"\n"
    if args.check:
        if AUDIT_PATH.read_text()!=rendered: print("audit.json differs from recomputed evidence"); return 1
        print("audit.json matches recomputed evidence")
        return 0
    else: AUDIT_PATH.write_text(rendered)
    print(json.dumps(data,indent=2,sort_keys=True)); return 0 if data["status"]=="verified" else 1
if __name__=="__main__": raise SystemExit(main())
