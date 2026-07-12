from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_one(code: str, seed: int, max_seconds: float):
    import game
    from reference_playbooks import REFERENCE_PLAYBOOKS, run_reference_playbook

    levels = {level.display_code: level for level in game.build_levels()}
    return run_reference_playbook(
        levels[code], REFERENCE_PLAYBOOKS[code], seed, max_seconds=max_seconds
    )


def parse_args():
    parser = argparse.ArgumentParser(description="Validate legal adventure reference playbooks")
    parser.add_argument("--seeds", type=int, default=20)
    parser.add_argument("--workers", type=int, default=max(1, min(12, os.cpu_count() or 1)))
    parser.add_argument("--max-seconds", type=float, default=900.0)
    parser.add_argument("--codes", nargs="*", default=[])
    parser.add_argument("--json-out", type=Path)
    return parser.parse_args()


def main() -> int:
    from reference_playbooks import REFERENCE_PLAYBOOKS, summarize_reference_results

    args = parse_args()
    codes = tuple(args.codes) if args.codes else tuple(REFERENCE_PLAYBOOKS)
    unknown = sorted(set(codes) - set(REFERENCE_PLAYBOOKS))
    if unknown:
        print(f"unknown level codes {', '.join(unknown)}")
        return 2
    seeds = tuple(range(max(0, args.seeds)))
    jobs = [(code, seed, args.max_seconds) for code in codes for seed in seeds]
    results = []
    with ProcessPoolExecutor(max_workers=max(1, args.workers)) as executor:
        futures = {executor.submit(run_one, *job): job for job in jobs}
        for future in as_completed(futures):
            code, seed, _ = futures[future]
            try:
                results.append(future.result())
            except Exception as exc:
                print(f"{code} seed {seed} crashed {exc}")
                return 2
            if len(results) % 50 == 0 or len(results) == len(jobs):
                print(f"completed {len(results)}/{len(jobs)}", flush=True)

    summaries = summarize_reference_results(results)
    for code in codes:
        summary = summaries[code]
        print(
            f"{code} wins={summary.wins} losses={summary.losses} "
            f"timeouts={summary.timeouts} win_rate={summary.win_rate:.0%} "
            f"slowest={summary.slowest_seconds:.0f}s"
        )
        for result in sorted(
            (item for item in results if item.code == code and item.outcome != "win"),
            key=lambda item: item.seed,
        ):
            print(f"  seed={result.seed} outcome={result.outcome} {result.diagnostic}")
    if args.json_out:
        payload = {
            "seeds": list(seeds),
            "max_seconds": args.max_seconds,
            "levels": {code: asdict(summaries[code]) for code in codes},
        }
        args.json_out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    failed = [
        summary
        for summary in summaries.values()
        if summary.win_rate < 0.90 or summary.timeouts > 0
    ]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
