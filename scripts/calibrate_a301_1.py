#!/usr/bin/env python3
"""
Operator-driven A301-1 dead-weight calibration runner (Bill 0003 path).

Walks one A301-1 channel through a fixed set of single dead weights, captures
each level via src.calibration.capture.CalibrationCapture (baseline -> onset ->
window, per Bill 0002 Part 3.2/3.3), fits F = a * raw^b, checks acceptance, and
writes the per-channel JSON record.

Force source: OIML-style single masses (measured values below). No stacking.
Per the operator's instruction, weights are used singly and not combined.

  53.0 g  -> 0.520 N
  103.9 g -> 1.019 N
  204.9 g -> 2.009 N
  507.0 g -> 4.972 N

DAQ: 8-channel custom DAQ on /dev/ttyUSB0 @ 115200 8N1, 18-byte frame
(0xAA start, 8x uint16-LE, 0x55 end), 12-bit ADC codes (0..4095). Protocol per
docs/toolchain_config.md "DAQ Serial Frame".

Usage:
    python3 scripts/calibrate_a301_1.py --channel 0 --operator shiyao

This is a bare-sensor / Bill 0003 dead-weight calibration. It does NOT attach a
TPUPadRecord (Bill 0004's TPUPadRecord admits only durometer "95A"; the bench
calibration feet are TPU 90A, so the fixture is recorded as a free-text note
rather than via the 95A-only record). The Case 2 / Case 3 sanity-check
conditions are not enforced by this script.
"""
from __future__ import annotations

import argparse
import struct
import sys
import time
from datetime import date
from pathlib import Path
from typing import Iterator, Sequence

import serial  # pyserial

# Make `src` importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import math  # noqa: E402

from src.calibration.deadweight import deadweight_force_N  # noqa: E402
from src.calibration.fit import check_acceptance, fit_power_law  # noqa: E402
from src.calibration.json_writer import (  # noqa: E402
    CalibrationPointRecord,
    write_calibration_json,
)
from src.calibration.deadweight import (  # noqa: E402
    DeadWeightRecord,
    build_deadweight_calibration_record,
)

# (measured mass in grams, OIML-ish certificate label) — single weights only.
DEFAULT_WEIGHTS_G = [53.0, 103.9, 204.9, 507.0]

START_BYTE = 0xAA
END_BYTE = 0x55
FRAME_DATA = 16  # 8 channels x uint16
CMD_START = bytes([0xFF])
CMD_STOP = bytes([0xFE])


def serial_frames(port: str, baud: int = 115200) -> Iterator[Sequence[int]]:
    """
    Yield [ts_ns, ch0..ch7] frames from the DAQ serial stream.

    Matches docs/toolchain_config.md DAQ Serial Frame: 0xAA, 8x uint16-LE, 0x55.
    Re-syncs on the start byte and validates the trailing end byte; malformed
    frames are skipped.
    """
    with serial.Serial(port, baud, timeout=1.0) as ser:
        ser.reset_input_buffer()
        ser.write(CMD_START)
        ser.flush()
        try:
            while True:
                b = ser.read(1)
                if not b:
                    continue
                if b[0] != START_BYTE:
                    continue
                payload = ser.read(FRAME_DATA + 1)  # data + end byte
                if len(payload) != FRAME_DATA + 1 or payload[-1] != END_BYTE:
                    continue  # desync; resync on next start byte
                chans = struct.unpack("<8H", payload[:FRAME_DATA])
                yield (time.monotonic_ns(), *chans)
        finally:
            try:
                ser.write(CMD_STOP)
                ser.flush()
            except Exception:
                pass


def _stats(samples: list[int]) -> tuple[float, float, float]:
    """Return (mean, std, drift_fraction) using the capture.py drift definition."""
    n = len(samples)
    mean = sum(samples) / n
    var = sum((x - mean) ** 2 for x in samples) / max(n - 1, 1)
    std = math.sqrt(var)
    half = n // 2
    mean_first = sum(samples[:half]) / max(half, 1)
    mean_second = sum(samples[half:]) / max(n - half, 1)
    drift = (mean_second - mean_first) / mean if mean else 0.0
    return mean, std, drift


def _read_samples(frames: Iterator[Sequence[int]], channel: int, n: int) -> list[int]:
    """Pull n consecutive raw ADC codes for one channel off the live stream."""
    out: list[int] = []
    for frame in frames:
        out.append(int(frame[channel + 1]))
        if len(out) >= n:
            break
    return out


def capture_once(
    frames: Iterator[Sequence[int]],
    channel: int,
    mass_g: float,
    sample_rate_hz: float,
    repeat_idx: int,
) -> tuple[float, float] | None:
    """
    One operator-paced capture, with retry.

    Flow (operator controls every step):
      1. Press Enter to capture baseline (sensor UNLOADED).
      2. Place the weight, let it settle, press Enter to capture the window.
      3. Review raw_mean / std / drift, then [a]ccept / [r]etry / [s]kip / [q]uit.

    Returns (window_mean, window_std) on accept, or None on skip.
    """
    applied_N = deadweight_force_N(mass_g / 1000.0)
    n_baseline = max(int(round(1.0 * sample_rate_hz)), 10)
    n_window = max(int(round(2.0 * sample_rate_hz)), 20)  # 200 @ 100 Hz

    while True:
        print(f"\n--- {mass_g:.1f} g -> {applied_N:.3f} N  (ch{channel}, repeat #{repeat_idx}) ---")
        input("  1. UNLOAD the sensor, then press Enter to capture baseline...")
        baseline = _read_samples(frames, channel, n_baseline)
        b_mean, b_std, _ = _stats(baseline)
        print(f"     baseline: mean={b_mean:.1f}  std={b_std:.1f}  (n={len(baseline)})")

        input(f"  2. Place the {mass_g:.1f} g weight, let it SETTLE, then press Enter to capture...")
        window = _read_samples(frames, channel, n_window)
        w_mean, w_std, drift = _stats(window)
        stationary = abs(drift) <= 0.05
        rise = w_mean - b_mean
        print(f"     window:   mean={w_mean:.1f}  std={w_std:.1f}  rise_over_baseline={rise:+.1f}")
        print(f"               drift={drift*100:+.1f}%  stationary={stationary}")
        if not stationary:
            print("     NOTE: drift > 5% — weight may still be settling, or it shifted.")
        if w_std > 0.10 * abs(w_mean) and w_mean:
            print("     NOTE: std is large vs mean — check seating / noise before accepting.")

        choice = input("  [a]ccept / [r]etry / [s]kip / [q]uit: ").strip().lower()
        if choice == "a":
            return w_mean, w_std
        if choice == "s":
            print(f"     skipped this capture.")
            return None
        if choice == "q":
            raise KeyboardInterrupt
        # anything else -> retry


def acquire_one_level(
    frames: Iterator[Sequence[int]],
    channel: int,
    mass_g: float,
    sample_rate_hz: float,
) -> tuple[CalibrationPointRecord, DeadWeightRecord] | None:
    """
    Capture one weight with operator-chosen repeats; average the accepted means.

    After each accepted capture the operator is asked whether to add another
    repeat (Bill 0002 Part 3.4). The averaged mean becomes the calibration
    point; raw_std is the spread across repeats when >1, else the window std.

    Returns the records, or None if no capture was accepted.
    """
    applied_N = deadweight_force_N(mass_g / 1000.0)
    captures: list[tuple[float, float]] = []  # (mean, std) per accepted repeat
    while True:
        result = capture_once(frames, channel, mass_g, sample_rate_hz, len(captures) + 1)
        if result is not None:
            captures.append(result)
        if not captures:
            return None  # skipped before any accept
        means = [m for m, _ in captures]
        avg = sum(means) / len(means)
        print(f"     {mass_g:.1f} g: {len(captures)} repeat(s) accepted, mean raw = {avg:.1f}")
        again = input("  another repeat of this weight? [y/N]: ").strip().lower()
        if again != "y":
            break

    means = [m for m, _ in captures]
    raw_mean = sum(means) / len(means)
    if len(means) > 1:
        mvar = sum((m - raw_mean) ** 2 for m in means) / (len(means) - 1)
        raw_std = math.sqrt(mvar)  # repeatability spread across repeats
    else:
        raw_std = captures[0][1]   # single window std

    weight = DeadWeightRecord(
        mass_kg=mass_g / 1000.0,
        oiml_class="uncertified",
        certificate_id=f"measured-{mass_g:.1f}g",
        traceable_to="bench scale (operator-measured)",
    )
    rec = CalibrationPointRecord(
        level_index=-1, applied_N=applied_N,
        raw_mean=raw_mean, raw_std=raw_std, repeats=len(captures),
    )
    return rec, weight


def main() -> int:
    ap = argparse.ArgumentParser(description="A301-1 dead-weight calibration runner")
    ap.add_argument("--channel", type=int, required=True, help="DAQ channel 0–4 (A301-1)")
    ap.add_argument("--operator", required=True)
    ap.add_argument("--port", default="/dev/ttyUSB0")
    ap.add_argument("--rate", type=float, default=100.0, help="DAQ sample rate (Hz)")
    ap.add_argument("--full-scale-n", type=float, default=15.0,
                    help="A301-1 FS in N (operator-confirmed 15 N config)")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--out", default="docs/calibration")
    ap.add_argument("--weights-g", type=float, nargs="+", default=DEFAULT_WEIGHTS_G,
                    help="single masses in grams (no stacking)")
    ap.add_argument("--monitor", action="store_true",
                    help="live raw readout for the channel; diagnose sensor response, then exit")
    args = ap.parse_args()

    if args.monitor:
        print(f"Live monitor — ch{args.channel} on {args.port}. Press/lift the sensor; Ctrl-C to quit.")
        print("Watch: does raw rise when loaded, return to baseline when unloaded, repeat consistently?")
        frames = serial_frames(args.port)
        win: list[int] = []
        try:
            for frame in frames:
                v = int(frame[args.channel + 1])
                win.append(v)
                if len(win) >= 10:  # ~10-sample smoothing
                    m = sum(win) / len(win)
                    lo, hi = min(win), max(win)
                    bar = "#" * int(min(m, 4095) / 4095 * 50)
                    print(f"\r raw≈{m:6.0f}  [min {lo:4d} max {hi:4d}]  {bar:<50}", end="", flush=True)
                    win = []
        except KeyboardInterrupt:
            print("\nmonitor stopped.")
            return 0

    print(f"A301-1 calibration — ch{args.channel}, operator {args.operator}, "
          f"{len(args.weights_g)} levels, FS {args.full_scale_n} N")
    print(f"DAQ: {args.port} @ 115200, {args.rate} Hz")
    print("Fixture note: bench calibration feet are TPU 90A (in load path).")

    frames = serial_frames(args.port)

    point_records: list[CalibrationPointRecord] = []
    weights: list[DeadWeightRecord] = []
    try:
        for mass_g in sorted(args.weights_g):
            result = acquire_one_level(frames, args.channel, mass_g, args.rate)
            if result is None:
                continue  # operator skipped this weight
            rec, weight = result
            point_records.append(CalibrationPointRecord(
                level_index=len(point_records), applied_N=rec.applied_N,
                raw_mean=rec.raw_mean, raw_std=rec.raw_std, repeats=rec.repeats,
            ))
            weights.append(weight)
    except KeyboardInterrupt:
        print("\nAborted by operator.", file=sys.stderr)
        return 130

    if len(point_records) < 3:
        print(f"\nNeed >=3 accepted levels to fit; got {len(point_records)}. "
              "Nothing written.", file=sys.stderr)
        return 2

    pts = [(p.raw_mean, p.applied_N) for p in point_records]
    fit = fit_power_law(pts)
    acc = check_acceptance(fit, full_scale_N=args.full_scale_n)

    print("\n=== FIT ===")
    print(f"  F = {fit.a:.6g} * raw^{fit.b:.6g}")
    print(f"  RMS residual   : {fit.rms_residual_N:.4f} N  (criterion {acc.rms_criterion_N:.4f} N)")
    print(f"  max |residual| : {fit.max_residual_N:.4f} N  (criterion {acc.max_criterion_N:.4f} N)")
    print(f"  adj-R^2 (log)  : {fit.adj_r_squared_loglog:.5f}  (criterion {acc.r_squared_criterion})")
    print(f"  ACCEPTED       : {acc.passed}")
    if not acc.passed:
        for f in acc.failures:
            print(f"    - {f}")

    record = build_deadweight_calibration_record(
        channel=args.channel,
        sensor_model="A301-1",
        physical_location=f"table-foot ch{args.channel}",
        calibration_date=args.date,
        operator=args.operator,
        full_scale_N=args.full_scale_n,
        quiescent_load_N=0.0,
        fit=fit,
        acceptance=acc,
        points=point_records,
        weights_used=weights,
    )
    record["fixture_note"] = "Bench calibration feet TPU 90A in load path; weights used singly (no stacking); masses operator-measured."

    out_path = write_calibration_json(record, output_dir=args.out)
    print(f"\nWrote {out_path}")
    return 0 if acc.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
