"""Run all training scripts in sequence."""
import subprocess, sys, time

scripts = [
    "train_skill_extractor.py",
    "train_job_matcher.py",
    "train_candidate_ranker.py",
    "train_sentiment.py",
    "train_offer_predictor.py",
]

total_start = time.time()
for i, script in enumerate(scripts, 1):
    print(f"\n{'='*60}")
    print(f"RUNNING {i}/{len(scripts)}: {script}")
    print(f"{'='*60}")
    start = time.time()
    result = subprocess.run([sys.executable, script], capture_output=False)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"✗ {script} FAILED (exit code {result.returncode})")
    else:
        print(f"✓ {script} completed in {elapsed:.1f}s")

total = time.time() - total_start
print(f"\n{'='*60}")
print(f"ALL SCRIPTS COMPLETE in {total:.1f}s")
print(f"{'='*60}")
