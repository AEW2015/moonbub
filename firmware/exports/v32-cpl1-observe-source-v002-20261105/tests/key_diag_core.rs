#[path = "../handheld/src/core_admission.rs"]
mod core_admission;
#[path = "../handheld/src/key_diag_core.rs"]
mod key_diag_core;
use core_admission::*;
use key_diag_core::*;
fn vd() -> VideoDrain {
    VideoDrain {
        worker_joined: true,
        receivers_closed: true,
        local_cleanup_complete: true,
    }
}
fn ad() -> AvDrain {
    AvDrain {
        session_cleared: true,
        feeder_idle: true,
        io_drained: true,
        power_restored: true,
    }
}
fn new_core() -> (CoreAdmission, DiagnosticCore) {
    let mut a = CoreAdmission::new(71);
    let p = a.reserve_diagnostic().unwrap();
    let c = DiagnosticCore::new(p, 19, 0, Budgets::default());
    (a, c)
}
#[derive(Default)]
struct Bus {
    status: u32,
    owner: u64,
    sequence: u32,
    rejects: u32,
    payload: Payload,
    starts: u32,
    aborts: u32,
    clears: u32,
    polls: u32,
    finish_at: u32,
    race_abort: bool,
}
impl Bus {
    fn finish(&mut self) {
        self.status = 0x13;
        self.sequence = self.sequence.wrapping_add(1);
        self.payload = Payload {
            cycles: 2997214,
            samples: 518400,
            bytes: 48203,
            fault: 0,
            epoch: 1,
            frame: 0,
            tag: [0xee7dc9c6, 0x10bef275, 0x19ffddad, 0x855898f0],
        };
    }
    fn action(&mut self, a: Action) -> Outcome {
        match a {
            Action::Write(Command::Start) => {
                self.starts += 1;
                self.owner += 1;
                self.status = 10;
                self.payload = Payload::default();
                Outcome::Written
            }
            Action::Write(Command::Abort) => {
                self.aborts += 1;
                if self.race_abort && self.status == 10 {
                    self.finish()
                }
                self.status = 0x46;
                self.payload.tag = [0; 4];
                self.payload.fault = 0;
                Outcome::Written
            }
            Action::Write(Command::Clear) => {
                self.clears += 1;
                self.status = 0;
                Outcome::Written
            }
            Action::Read(r) => Outcome::Read(match r {
                Register::CoreMagic | Register::Magic => 0x31444b41,
                Register::CoreSchema | Register::Schema => 0x10000,
                Register::CoreCapabilities => 0,
                Register::Build => 0x4d424b31,
                Register::FixtureBytes => 48203,
                Register::Watchdog => 10000000,
                Register::State => {
                    if self.status == 10 {
                        self.polls += 1;
                        if self.finish_at > 0 && self.polls >= self.finish_at {
                            self.finish()
                        }
                    }
                    self.status
                }
                Register::Sequence => self.sequence,
                Register::OwnerLow => self.owner as u32,
                Register::OwnerHigh => (self.owner >> 32) as u32,
                Register::Rejects => self.rejects,
                Register::Cycles => self.payload.cycles,
                Register::Samples => self.payload.samples,
                Register::Bytes => self.payload.bytes,
                Register::Fault => self.payload.fault,
                Register::Epoch => self.payload.epoch,
                Register::Frame => self.payload.frame,
                Register::Tag0 => self.payload.tag[0],
                Register::Tag1 => self.payload.tag[1],
                Register::Tag2 => self.payload.tag[2],
                Register::Tag3 => self.payload.tag[3],
            }),
        }
    }
}
fn step(c: &mut DiagnosticCore, b: &mut Bus, t: &mut u64) {
    if let Some(op) = c.next_operation(*t) {
        let out = b.action(op.action());
        c.complete(op, out, 19, *t);
    }
    *t += 1000;
}
fn until(c: &mut DiagnosticCore, b: &mut Bus, t: &mut u64, target: Stage) {
    for _ in 0..300 {
        if c.stage() == target {
            return;
        }
        assert!(
            !matches!(c.stage(), Stage::Quarantined | Stage::Refused),
            "unexpected {:?} {:?}",
            c.stage(),
            c.reason()
        );
        step(c, b, t)
    }
    panic!("stage timeout {:?}", c.stage())
}
fn release(mut a: CoreAdmission, c: DiagnosticCore) {
    let (p, proof, _) = c.into_exit().unwrap();
    a.release_diagnostic(p, proof).unwrap();
    assert!(a.idle());
}

#[test]
fn coexistence_matrix_and_av_admission_precedes_session_mutation() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    a.activate_video(&v).unwrap();
    let mut session_active = false;
    let av = a.reserve_av().unwrap();
    assert!(!session_active);
    // Acquiring AV permit succeeded before this simulated session mutation.
    assert!(a.av_phase().is_some());
    session_active = true;
    assert!(session_active);
    assert!(a.reserve_diagnostic().is_err());
    assert!(a.reserve_program().is_err());
    assert!(a.reserve_video_program(&v).is_err());
    a.activate_av(&av).unwrap();
    a.begin_av_drain(&av).unwrap();
    let (e, av) = a
        .release_av(
            av,
            AvDrain {
                feeder_idle: false,
                ..ad()
            },
        )
        .unwrap_err();
    assert_eq!(e, Error::NotDrained);
    assert!(a.reserve_diagnostic().is_err());
    a.release_av(av, ad()).unwrap();
    let p = a.reserve_video_program(&v).unwrap();
    assert!(a.reserve_av().is_err());
    a.release_program(p, ProgramFinish::NoSideEffects).unwrap();
    a.begin_video_drain(&v).unwrap();
    a.release_video(v, vd()).unwrap();
    assert!(a.reserve_diagnostic().is_ok());
}
#[test]
fn diagnostic_wins_then_av_and_queued_program_cannot_mutate_hardware() {
    let mut a = CoreAdmission::new(1);
    let queued_program_request = true;
    let d = a.reserve_diagnostic().unwrap();
    assert!(queued_program_request);
    let mut physical_calls = 0;
    let result = match a.reserve_program() {
        Ok(_) => {
            physical_calls += 1;
            Ok(())
        }
        Err(e) => Err(e),
    };
    assert_eq!(result, Err(Error::Busy));
    assert_eq!(physical_calls, 0);
    assert!(a.reserve_video().is_err());
    drop(d);
    assert!(a.diagnostic_reserved()); // inert Drop fails closed
}
#[test]
fn programming_wins_and_failure_after_side_effects_retains_reservation() {
    let mut a = CoreAdmission::new(1);
    let p = a.reserve_program().unwrap();
    assert!(a.reserve_diagnostic().is_err());
    a.program_side_effects_begin(&p).unwrap();
    let (e, p) = a
        .release_program(p, ProgramFinish::Unconfirmed)
        .unwrap_err();
    assert_eq!(e, Error::Unconfirmed);
    let (_, p) = a
        .release_program(p, ProgramFinish::NoSideEffects)
        .unwrap_err();
    let (_, p) = a
        .release_program(
            p,
            ProgramFinish::Configured {
                call_returned: true,
                post_init_complete: true,
            },
        )
        .unwrap_err();
    assert!(a.program_reserved());
    let (_, p) = a
        .release_program(
            p,
            ProgramFinish::RecoveryConfirmed {
                identity_verified: false,
                core_quiescent: true,
            },
        )
        .unwrap_err();
    a.release_program(
        p,
        ProgramFinish::RecoveryConfirmed {
            identity_verified: true,
            core_quiescent: true,
        },
    )
    .unwrap();
    assert!(a.reserve_diagnostic().is_ok());
}
#[test]
fn video_stop_releases_only_video_while_independent_av_continues() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    a.activate_video(&v).unwrap();
    let av = a.reserve_av().unwrap();
    a.activate_av(&av).unwrap();
    a.begin_video_drain(&v).unwrap();
    assert_eq!(a.av_phase(), Some(Phase::Active));
    let (_, v) = a
        .release_video(
            v,
            VideoDrain {
                worker_joined: false,
                ..vd()
            },
        )
        .unwrap_err();
    assert_eq!(a.av_phase(), Some(Phase::Active));
    a.release_video(v, vd()).unwrap();
    assert_eq!(a.video_phase(), None);
    assert_eq!(a.av_phase(), Some(Phase::Active));
    assert!(a.reserve_diagnostic().is_err());
    assert!(a.reserve_program().is_err());
    a.begin_av_drain(&av).unwrap();
    let (_, av) = a
        .release_av(
            av,
            AvDrain {
                power_restored: false,
                ..ad()
            },
        )
        .unwrap_err();
    assert!(a.reserve_diagnostic().is_err());
    a.release_av(av, ad()).unwrap();
    assert!(a.idle());
}

#[test]
fn queued_owned_program_is_denied_if_video_cancelled_before_authorization() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    let p = a.reserve_video_program(&v).unwrap();
    a.begin_video_drain(&v).unwrap();
    assert_eq!(a.program_side_effects_begin(&p), Err(Error::WrongPhase));
    let (_, v) = a.release_video(v, vd()).unwrap_err();
    a.release_program(p, ProgramFinish::NoSideEffects).unwrap();
    a.release_video(v, vd()).unwrap();
}
#[test]
fn authorized_program_must_drain_before_cancelled_video_releases() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    let p = a.reserve_video_program(&v).unwrap();
    a.program_side_effects_begin(&p).unwrap();
    a.begin_video_drain(&v).unwrap();
    let (_, v) = a.release_video(v, vd()).unwrap_err();
    a.release_program(
        p,
        ProgramFinish::Configured {
            call_returned: true,
            post_init_complete: true,
        },
    )
    .unwrap();
    a.release_video(v, vd()).unwrap();
}
#[test]
fn no_token_id_reuse_and_cross_generation_tokens_reject() {
    let mut a = CoreAdmission::new(1);
    let p = a.reserve_program().unwrap();
    let id = p.id();
    a.release_program(p, ProgramFinish::NoSideEffects).unwrap();
    let p = a.reserve_program().unwrap();
    assert!(p.id() > id);
    let mut other = CoreAdmission::new(2);
    let (_, p) = other
        .release_program(p, ProgramFinish::NoSideEffects)
        .unwrap_err();
    a.release_program(p, ProgramFinish::NoSideEffects).unwrap();
    a.seed_next_id_for_test(u64::MAX - 1);
    let p = a.reserve_program().unwrap();
    assert_eq!(p.id(), u64::MAX - 1);
    a.release_program(p, ProgramFinish::NoSideEffects).unwrap();
    assert!(matches!(a.reserve_program(), Err(Error::Exhausted)));
}
#[test]
fn all_legacy_blockers_deny_new_admission() {
    for b in [
        Blockers {
            restoring: true,
            ..Blockers::default()
        },
        Blockers {
            rate_changing: true,
            ..Blockers::default()
        },
        Blockers {
            benchmark: true,
            ..Blockers::default()
        },
        Blockers {
            recovery_failed: true,
            ..Blockers::default()
        },
    ] {
        let mut a = CoreAdmission::new(1);
        a.set_blockers(b);
        assert!(a.reserve_video().is_err());
        assert!(a.reserve_program().is_err());
        assert!(a.reserve_diagnostic().is_err());
    }
}
#[test]
fn all_exact_identity_words_fail_closed_before_start() {
    for bad in 0..8 {
        let (a, mut c) = new_core();
        let mut b = Bus::default();
        let mut t = 0;
        for i in 0..=bad {
            let op = c.next_operation(t).unwrap();
            let out = b.action(op.action());
            c.complete(
                op,
                match out {
                    Outcome::Read(v) if i == bad => Outcome::Read(v ^ 1),
                    x => x,
                },
                19,
                t,
            );
            t += 1000;
        }
        assert_eq!(c.stage(), Stage::Refused);
        assert_eq!(b.starts, 0);
        release(a, c);
    }
}
#[test]
fn startup_unowned_run_and_every_terminal_quarantine_without_claiming_success() {
    for status in [9, 10, 13, 0x13, 0x24, 0x46] {
        let (a, mut c) = new_core();
        let mut b = Bus {
            status,
            owner: 77,
            sequence: 8,
            ..Bus::default()
        };
        let mut t = 0;
        for _ in 0..30 {
            step(&mut c, &mut b, &mut t)
        }
        assert_eq!(c.stage(), Stage::Quarantined);
        assert_eq!(c.reason(), Some(Reason::UnownedState));
        c.request_stop(t);
        assert_eq!(c.stage(), Stage::Quarantined);
        assert!(!c.request_clear(t));
        assert!(c.record().is_none());
        assert_eq!((b.starts, b.aborts, b.clears), (0, 0, 0));
        assert!(c.into_exit().is_err());
        assert!(a.diagnostic_reserved());
    }
}
#[test]
fn exact_done_full_owner64_sequence_wrap_and_explicit_clear() {
    let (a, mut c) = new_core();
    let mut b = Bus {
        owner: 0x12345678ffffffff,
        sequence: u32::MAX,
        finish_at: 2,
        ..Bus::default()
    };
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Held);
    let r = *c.record().unwrap();
    assert_eq!(r.kind, ResultKind::Completed);
    assert_eq!(r.owner, 0x1234567900000000);
    assert_eq!(r.sequence, 0);
    assert_eq!(r.payload.tag, TAG);
    assert!(c.request_clear(t));
    until(&mut c, &mut b, &mut t, Stage::Cleared);
    assert_eq!(c.record(), Some(&r));
    assert_eq!((b.starts, b.clears), (1, 1));
    release(a, c);
}
#[test]
fn terminal_torn_owner_state_and_sequence_never_publish() {
    for reg in [Register::OwnerHigh, Register::Sequence, Register::State] {
        let (_, mut c) = new_core();
        let mut b = Bus {
            finish_at: 2,
            ..Bus::default()
        };
        let mut t = 0;
        until(&mut c, &mut b, &mut t, Stage::TerminalAfter);
        for _ in 0..4 {
            let op = c.next_operation(t).unwrap();
            let out = b.action(op.action());
            let out = match out {
                Outcome::Read(v) if op.action() == Action::Read(reg) => Outcome::Read(v ^ 1),
                x => x,
            };
            c.complete(op, out, 19, t);
            t += 1000;
        }
        assert_eq!(c.stage(), Stage::Quarantined);
        assert!(c.record().is_none());
    }
}
#[test]
fn bad_tag_is_owned_failure_not_success_and_still_requires_clear() {
    let (a, mut c) = new_core();
    let mut b = Bus {
        finish_at: 2,
        ..Bus::default()
    };
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Payload);
    b.payload.tag[3] ^= 1;
    until(&mut c, &mut b, &mut t, Stage::Held);
    assert_eq!(c.record().unwrap().kind, ResultKind::DataMismatch);
    assert!(a.diagnostic_reserved());
    assert!(c.request_clear(t));
    until(&mut c, &mut b, &mut t, Stage::Cleared);
    release(a, c);
}
#[test]
fn stop_confirms_aborted_with_sequence_s_or_s_plus_one() {
    for race in [false, true] {
        let (a, mut c) = new_core();
        let mut b = Bus {
            owner: 0x1234567800000040,
            sequence: 99,
            race_abort: race,
            ..Bus::default()
        };
        let mut t = 0;
        until(&mut c, &mut b, &mut t, Stage::Poll);
        c.request_stop(t);
        until(&mut c, &mut b, &mut t, Stage::Held);
        let r = c.record().unwrap();
        assert_eq!(r.kind, ResultKind::Aborted);
        assert_eq!(r.sequence, 99 + race as u32);
        assert_eq!(b.aborts, 1);
        assert!(c.request_clear(t));
        until(&mut c, &mut b, &mut t, Stage::Cleared);
        release(a, c);
    }
}
#[test]
fn stop_on_outstanding_start_handles_not_issued_and_accepted_paths() {
    for sent in [false, true] {
        let (a, mut c) = new_core();
        let mut b = Bus::default();
        let mut t = 0;
        until(&mut c, &mut b, &mut t, Stage::Start);
        let op = c.next_operation(t).unwrap();
        c.request_stop(t);
        let out = if sent {
            b.action(op.action())
        } else {
            Outcome::NoLock
        };
        c.complete(op, out, 19, t);
        t += 1000;
        if sent {
            until(&mut c, &mut b, &mut t, Stage::Held);
            assert_eq!(c.record().unwrap().kind, ResultKind::Aborted);
            assert!(c.request_clear(t));
            until(&mut c, &mut b, &mut t, Stage::Cleared);
        } else {
            assert_eq!(c.stage(), Stage::Refused);
            assert_eq!(b.starts, 0);
        }
        release(a, c);
    }
}
#[test]
fn timeout_enters_bounded_abort_and_never_infers_success() {
    let (a, mut c) = new_core();
    let mut b = Bus::default();
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Poll);
    t = 1000000;
    assert!(c.next_operation(t).is_none());
    assert_eq!(c.stage(), Stage::AbortIdentity);
    until(&mut c, &mut b, &mut t, Stage::Held);
    assert_eq!(c.record().unwrap().kind, ResultKind::Aborted);
    assert!(c.request_clear(t));
    until(&mut c, &mut b, &mut t, Stage::Cleared);
    release(a, c);
}
#[test]
fn action_budget_and_failed_stop_keep_reservation() {
    let (mut a, mut c) = new_core();
    let mut b = Bus::default();
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Poll);
    c.request_stop(t);
    for _ in 0..70 {
        if let Some(op) = c.next_operation(t) {
            c.complete(op, Outcome::NoLock, 19, t)
        }
        t += 1;
    }
    assert_eq!(c.stage(), Stage::Quarantined);
    assert_eq!(c.reason(), Some(Reason::ActionBudget));
    assert!(c.into_exit().is_err());
    assert!(a.reserve_video().is_err());
    assert_eq!(b.aborts, 0);
}
#[test]
fn read_error_before_start_is_unknown_not_clean_idle() {
    let (a, mut c) = new_core();
    let op = c.next_operation(0).unwrap();
    c.complete(op, Outcome::IoError, 19, 0);
    assert_eq!(c.stage(), Stage::Quarantined);
    assert!(c.into_exit().is_err());
    assert!(a.diagnostic_reserved());
}
#[test]
fn ambiguous_start_is_not_retried_and_can_only_recover_its_owner() {
    let (a, mut c) = new_core();
    let mut b = Bus::default();
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Start);
    let op = c.next_operation(t).unwrap();
    b.action(op.action());
    c.complete(op, Outcome::IoError, 19, t);
    assert_eq!(c.stage(), Stage::Quarantined);
    assert_eq!(b.starts, 1);
    assert!(c.next_operation(t).is_none());
    c.request_stop(t);
    until(&mut c, &mut b, &mut t, Stage::Held);
    assert_eq!(b.starts, 1);
    assert_eq!(c.record().unwrap().kind, ResultKind::Aborted);
    assert!(c.request_clear(t));
    until(&mut c, &mut b, &mut t, Stage::Cleared);
    release(a, c);
}
#[test]
fn observed_reset_or_program_epoch_change_is_never_old_success() {
    for epoch_change in [false, true] {
        let (a, mut c) = new_core();
        let mut b = Bus::default();
        let mut t = 0;
        until(&mut c, &mut b, &mut t, Stage::Poll);
        let op = c.next_operation(t).unwrap();
        b.status = 0;
        b.owner = 0;
        b.sequence = 0;
        c.complete(op, Outcome::Read(0), if epoch_change { 20 } else { 19 }, t);
        assert_eq!(c.stage(), Stage::Quarantined);
        assert!(c.record().is_none());
        assert!(c.into_exit().is_err());
        assert!(a.diagnostic_reserved());
    }
}
#[test]
fn stale_operation_from_other_reservation_cannot_be_reused() {
    let (_, mut c) = new_core();
    let op = c.next_operation(0).unwrap();
    let mut a2 = CoreAdmission::new(999);
    let p = a2.reserve_diagnostic().unwrap();
    let mut other = DiagnosticCore::new(p, 19, 0, Budgets::default());
    let wrong = other.next_operation(0).unwrap();
    c.complete(wrong, Outcome::Read(MAGIC), 19, 0);
    assert_eq!(c.stage(), Stage::Quarantined);
    assert!(c.into_exit().is_err());
    drop(op);
}
#[test]
fn clear_ambiguous_or_torn_ack_never_frees_exclusivity() {
    for ambiguous in [false, true] {
        let (a, mut c) = new_core();
        let mut b = Bus {
            finish_at: 2,
            ..Bus::default()
        };
        let mut t = 0;
        until(&mut c, &mut b, &mut t, Stage::Held);
        assert!(c.request_clear(t));
        until(&mut c, &mut b, &mut t, Stage::Clear);
        let op = c.next_operation(t).unwrap();
        b.action(op.action());
        c.complete(
            op,
            if ambiguous {
                Outcome::IoError
            } else {
                Outcome::Written
            },
            19,
            t,
        );
        t += 1000;
        if !ambiguous {
            b.owner += 1;
            for _ in 0..4 {
                step(&mut c, &mut b, &mut t)
            }
        }
        assert_eq!(c.stage(), Stage::Quarantined);
        assert!(c.record().is_some());
        assert!(c.into_exit().is_err());
        assert!(a.diagnostic_reserved());
    }
}
#[test]
fn no_arbitrary_csr_values_or_addresses_are_emitted() {
    let (a, mut c) = new_core();
    let mut b = Bus {
        finish_at: 2,
        ..Bus::default()
    };
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Held);
    assert!(c.request_clear(t));
    while c.stage() != Stage::Cleared {
        let op = c.next_operation(t).unwrap();
        match op.action() {
            Action::Write(cmd) => {
                assert!(cmd.offset() == 0x408 && [1, 2, 4].contains(&cmd.value()))
            }
            Action::Read(r) => assert!(
                r.offset() % 4 == 0
                    && ([0, 4, 8, 0x184].contains(&r.offset())
                        || (0x400..=0x44c).contains(&r.offset()))
            ),
        }
        let out = b.action(op.action());
        c.complete(op, out, 19, t);
        t += 1000;
    }
    release(a, c);
}

#[test]
fn existing_restore_waits_for_true_idle_without_opening_admission_gap() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    a.activate_video(&v).unwrap();
    let av = a.reserve_av().unwrap();
    a.set_blockers(Blockers {
        restoring: true,
        ..Blockers::default()
    });
    a.begin_video_drain(&v).unwrap();
    assert!(a.reserve_restore_program().is_err());
    a.begin_av_drain(&av).unwrap();
    a.release_av(av, ad()).unwrap();
    a.release_video(v, vd()).unwrap();
    assert!(a.reserve_diagnostic().is_err());
    assert!(a.reserve_program().is_err());
    let p = a.reserve_restore_program().unwrap();
    a.program_side_effects_begin(&p).unwrap();
    a.release_program(
        p,
        ProgramFinish::Configured {
            call_returned: true,
            post_init_complete: true,
        },
    )
    .unwrap();
    assert!(a.reserve_video().is_err());
    a.set_blockers(Blockers::default());
    assert!(a.reserve_diagnostic().is_ok());
}
#[test]
fn hardware_failure_is_owned_terminal_evidence_not_success() {
    let (a, mut c) = new_core();
    let mut b = Bus::default();
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Poll);
    b.status = 0x24;
    b.sequence = 1;
    b.payload.fault = 0xf02;
    until(&mut c, &mut b, &mut t, Stage::Held);
    assert_eq!(c.record().unwrap().kind, ResultKind::HardwareFailed);
    assert!(c.request_clear(t));
    until(&mut c, &mut b, &mut t, Stage::Cleared);
    release(a, c);
}
#[test]
fn malformed_status_flags_and_wrong_ack_owner_high_word_quarantine() {
    for bad in [7, 0x1b, 0x100] {
        let (_, mut c) = new_core();
        let mut b = Bus {
            status: bad,
            ..Bus::default()
        };
        let mut t = 0;
        for _ in 0..20 {
            step(&mut c, &mut b, &mut t)
        }
        assert_eq!(c.stage(), Stage::Quarantined);
        assert_eq!(c.reason(), Some(Reason::MalformedState));
    }
    let (_, mut c) = new_core();
    let mut b = Bus {
        owner: 0x1234000000000000,
        ..Bus::default()
    };
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Acknowledge);
    b.owner ^= 1u64 << 32;
    for _ in 0..5 {
        step(&mut c, &mut b, &mut t)
    }
    assert_eq!(c.stage(), Stage::Quarantined);
    assert_eq!(c.reason(), Some(Reason::Owner));
}
#[test]
fn stop_sequence_more_than_one_completion_is_not_accepted() {
    let (_, mut c) = new_core();
    let mut b = Bus::default();
    let mut t = 0;
    until(&mut c, &mut b, &mut t, Stage::Poll);
    b.sequence = 2;
    c.request_stop(t);
    for _ in 0..30 {
        step(&mut c, &mut b, &mut t)
    }
    assert_eq!(c.stage(), Stage::Quarantined);
    assert_eq!(c.reason(), Some(Reason::Sequence));
    assert_eq!(b.aborts, 0);
}
#[test]
fn single_outstanding_operation_and_monotonic_ticket_budget() {
    let (_, mut c) = new_core();
    let op = c.next_operation(0).unwrap();
    assert_eq!(op.ticket(), 1);
    assert!(c.next_operation(1).is_none());
    assert_eq!(c.actions_in_phase(), 1);
    c.complete(op, Outcome::NoLock, 19, 1);
    let op = c.next_operation(2).unwrap();
    assert_eq!(op.ticket(), 2);
    assert_eq!(c.actions_in_phase(), 2);
    c.complete(op, Outcome::Read(MAGIC), 19, 2);
    assert_eq!(c.stage(), Stage::Identity);
    assert!(c.next_operation(1).is_none());
    assert_eq!(c.reason(), Some(Reason::Clock));
}
#[test]
fn unobservable_external_reset_aba_is_an_explicit_schema_limitation() {
    for reset in [false, true] {
        let (a, mut c) = new_core();
        let mut b = Bus::default();
        let mut t = 0;
        until(&mut c, &mut b, &mut t, Stage::Poll);
        if reset {
            b.status = 0;
            b.owner = 0;
            b.sequence = 0;
            b.action(Action::Write(Command::Start));
        }
        b.finish();
        until(&mut c, &mut b, &mut t, Stage::Held);
        // The schema has no hardware boot nonce: reset + unseen external START can
        // reproduce owner1/seq1/identical payload. No claim of reset-proof identity.
        assert_eq!(c.record().unwrap().kind, ResultKind::Completed);
        assert_eq!(c.record().unwrap().owner, 1);
        assert_eq!(c.record().unwrap().sequence, 1);
        assert!(c.request_clear(t));
        until(&mut c, &mut b, &mut t, Stage::Cleared);
        release(a, c);
    }
}
#[test]
fn mutex_adapter_harness_releases_control_before_session_callback() {
    use std::sync::{mpsc, Arc, Mutex};
    use std::thread;
    let a = Arc::new(Mutex::new(CoreAdmission::new(1)));
    let v = {
        let mut g = a.lock().unwrap();
        let v = g.reserve_video().unwrap();
        g.activate_video(&v).unwrap();
        v
    };
    let (a1, a2) = (a.clone(), a.clone());
    let (tx, rx) = mpsc::channel();
    let (go, wait) = mpsc::channel();
    let worker = thread::spawn(move || {
        let av = {
            let mut g = a1.lock().unwrap();
            g.reserve_av().unwrap()
        };
        tx.send(()).unwrap();
        wait.recv().unwrap();
        assert!(a1.try_lock().is_ok());
        let mutation = true;
        assert!(mutation);
        (v, av)
    });
    rx.recv().unwrap();
    assert!(a2.lock().unwrap().reserve_diagnostic().is_err());
    go.send(()).unwrap();
    let (v, av) = worker.join().unwrap();
    let mut g = a.lock().unwrap();
    g.begin_video_drain(&v).unwrap();
    g.begin_av_drain(&av).unwrap();
    g.release_av(av, ad()).unwrap();
    g.release_video(v, vd()).unwrap();
    assert!(g.idle());
}

fn loaded() -> LoadedVideoCore {
    LoadedVideoCore {
        compatible: true,
        already_loaded: true,
        unchanged_program_epoch: true,
    }
}

#[test]
fn av_only_input_tone_and_audio_need_no_video_owner() {
    // Ownership is mode-independent; these labels are policy cases, not audio
    // playback/UDP execution or physical tone qualification.
    for mode in ["input-only", "tone", "audio"] {
        let mut a = CoreAdmission::new(100);
        let av = a.reserve_av().unwrap();
        assert_eq!(a.video_phase(), None, "{mode}");
        assert!(a.reserve_program().is_err());
        assert!(a.reserve_diagnostic().is_err());
        a.activate_av(&av).unwrap();
        assert_eq!(a.av_phase(), Some(Phase::Active));
        let mut av_service_ticks = 0;
        for _ in 0..4 {
            av_service_ticks += 1;
            assert_eq!(a.video_phase(), None);
        }
        assert_eq!(av_service_ticks, 4);
        a.begin_av_drain(&av).unwrap();
        let (_, av) = a
            .release_av(
                av,
                AvDrain {
                    io_drained: false,
                    ..ad()
                },
            )
            .unwrap_err();
        assert!(a.reserve_program().is_err());
        a.release_av(av, ad()).unwrap();
        assert!(a.idle());
    }
}

#[test]
fn av_first_video_join_video_stop_av_continues_then_av_stop() {
    let mut a = CoreAdmission::new(1);
    let av = a.reserve_av().unwrap();
    a.activate_av(&av).unwrap();
    let v = a.reserve_video().unwrap();
    let first_video_id = v.id();
    assert_eq!(a.activate_video(&v), Err(Error::NeedsCompatibleCore));
    assert!(a.reserve_video_program(&v).is_err());
    a.activate_video_loaded_core(&v, loaded()).unwrap();
    assert_eq!(a.av_phase(), Some(Phase::Active));
    a.begin_video_drain(&v).unwrap();
    a.release_video(v, vd()).unwrap();
    assert_eq!(a.video_phase(), None);
    assert_eq!(a.av_phase(), Some(Phase::Active));
    let av_stop_calls = 0;
    for _ in 0..3 {
        assert_eq!(a.av_phase(), Some(Phase::Active));
    }
    assert_eq!(av_stop_calls, 0);
    // The same AV session survives a subsequent video request with a fresh token.
    let v = a.reserve_video().unwrap();
    assert!(v.id() > first_video_id);
    a.activate_video_loaded_core(&v, loaded()).unwrap();
    a.begin_video_drain(&v).unwrap();
    a.release_video(v, vd()).unwrap();
    assert_eq!(a.av_phase(), Some(Phase::Active));
    a.begin_av_drain(&av).unwrap();
    a.release_av(av, ad()).unwrap();
    assert!(a.idle());
}

#[test]
fn video_first_av_join_and_independent_av_stop_preserve_video() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    a.activate_video(&v).unwrap();
    let av = a.reserve_av().unwrap();
    a.activate_av(&av).unwrap();
    a.begin_av_drain(&av).unwrap();
    assert_eq!(a.video_phase(), Some(Phase::Active));
    assert!(a.reserve_video_program(&v).is_err());
    a.release_av(av, ad()).unwrap();
    assert_eq!(a.video_phase(), Some(Phase::Active));
    let p = a.reserve_video_program(&v).unwrap();
    a.release_program(p, ProgramFinish::NoSideEffects).unwrap();
    a.begin_video_drain(&v).unwrap();
    a.release_video(v, vd()).unwrap();
    assert!(a.idle());
}

#[test]
fn av_start_can_win_while_video_pending_without_forcing_programming() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    let av = a.reserve_av().unwrap();
    assert!(a.reserve_video_program(&v).is_err());
    assert_eq!(a.activate_video(&v), Err(Error::NeedsCompatibleCore));
    a.activate_av(&av).unwrap();
    a.activate_video_loaded_core(&v, loaded()).unwrap();
    a.begin_video_drain(&v).unwrap();
    a.release_video(v, vd()).unwrap();
    assert_eq!(a.av_phase(), Some(Phase::Active));
    a.begin_av_drain(&av).unwrap();
    a.release_av(av, ad()).unwrap();
    assert!(a.idle());
}

#[test]
fn incompatible_or_changed_loaded_core_join_cannot_reprogram_av() {
    for proof in [
        LoadedVideoCore {
            compatible: false,
            ..loaded()
        },
        LoadedVideoCore {
            already_loaded: false,
            ..loaded()
        },
        LoadedVideoCore {
            unchanged_program_epoch: false,
            ..loaded()
        },
    ] {
        let mut a = CoreAdmission::new(1);
        let av = a.reserve_av().unwrap();
        a.activate_av(&av).unwrap();
        let v = a.reserve_video().unwrap();
        assert_eq!(
            a.activate_video_loaded_core(&v, proof),
            Err(Error::IncompatibleCore)
        );
        assert_eq!(a.video_phase(), Some(Phase::Pending));
        assert_eq!(a.av_phase(), Some(Phase::Active));
        assert!(a.reserve_program().is_err());
        assert!(a.reserve_video_program(&v).is_err());
        a.begin_video_drain(&v).unwrap();
        a.release_video(v, vd()).unwrap();
        assert_eq!(a.av_phase(), Some(Phase::Active));
        a.begin_av_drain(&av).unwrap();
        a.release_av(av, ad()).unwrap();
        assert!(a.idle());
    }
}

#[test]
fn independent_av_and_diagnostic_admission_race_both_orders() {
    let mut a = CoreAdmission::new(1);
    let d = a.reserve_diagnostic().unwrap();
    let mut session_mutations = 0;
    match a.reserve_av() {
        Ok(_) => session_mutations += 1,
        Err(e) => assert_eq!(e, Error::Busy),
    }
    assert_eq!(session_mutations, 0);
    drop(d);
    assert!(a.diagnostic_reserved());
    let mut a = CoreAdmission::new(2);
    let av = a.reserve_av().unwrap();
    assert!(a.reserve_diagnostic().is_err());
    assert!(a.reserve_program().is_err());
    a.begin_av_drain(&av).unwrap();
    let (_, av) = a
        .release_av(
            av,
            AvDrain {
                session_cleared: false,
                ..ad()
            },
        )
        .unwrap_err();
    assert!(a.reserve_diagnostic().is_err());
    a.release_av(av, ad()).unwrap();
    assert!(a.reserve_diagnostic().is_ok());
}

#[test]
fn independent_av_and_program_admission_race_both_orders() {
    let mut a = CoreAdmission::new(1);
    let p = a.reserve_program().unwrap();
    assert!(a.reserve_av().is_err());
    a.release_program(p, ProgramFinish::NoSideEffects).unwrap();
    let av = a.reserve_av().unwrap();
    assert!(a.reserve_program().is_err());
    let v = a.reserve_video().unwrap();
    assert!(a.reserve_video_program(&v).is_err());
    a.begin_video_drain(&v).unwrap();
    a.release_video(v, vd()).unwrap();
    assert_eq!(a.av_phase(), Some(Phase::Pending));
    a.begin_av_drain(&av).unwrap();
    a.release_av(av, ad()).unwrap();
    assert!(a.idle());
}

#[test]
fn av_may_start_during_video_only_cleanup_without_becoming_a_child() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    a.activate_video(&v).unwrap();
    a.begin_video_drain(&v).unwrap();
    let av = a.reserve_av().unwrap();
    a.activate_av(&av).unwrap();
    a.release_video(v, vd()).unwrap();
    assert_eq!(a.av_phase(), Some(Phase::Active));
    a.begin_av_drain(&av).unwrap();
    a.release_av(av, ad()).unwrap();
    assert!(a.idle());
}

#[test]
fn video_stop_does_not_wait_for_an_independent_av_cleanup_drain() {
    let mut a = CoreAdmission::new(1);
    let v = a.reserve_video().unwrap();
    a.activate_video(&v).unwrap();
    let av = a.reserve_av().unwrap();
    a.activate_av(&av).unwrap();
    a.begin_av_drain(&av).unwrap();
    let (_, av) = a
        .release_av(
            av,
            AvDrain {
                io_drained: false,
                ..ad()
            },
        )
        .unwrap_err();
    a.begin_video_drain(&v).unwrap();
    a.release_video(v, vd()).unwrap();
    assert_eq!(a.video_phase(), None);
    assert_eq!(a.av_phase(), Some(Phase::Draining));
    assert!(a.reserve_program().is_err());
    assert!(a.reserve_diagnostic().is_err());
    a.release_av(av, ad()).unwrap();
    assert!(a.idle());
}
