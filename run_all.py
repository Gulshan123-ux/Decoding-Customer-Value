"""
=============================================================
DECODING CUSTOMER VALUE — Master Runner
Run this to execute the full pipeline end-to-end.
=============================================================
"""
import subprocess, sys, os

steps = [
    ("Step 1 — Data Preparation & Feature Engineering", "01_data_preparation.py"),
    ("Step 2 — RFM Segmentation & Visualisations",      "02_rfm_segmentation.py"),
    ("Step 4 — Retention Playbook & Executive Summary", "04_retention_playbook.py"),
]

print("="*60)
print("  DECODING CUSTOMER VALUE — Full Pipeline")
print("="*60)

for label, script in steps:
    print(f"\n{'─'*60}")
    print(f"▶ {label}")
    print(f"  Running: {script}")
    print(f"{'─'*60}")
    result = subprocess.run([sys.executable, script], capture_output=False)
    if result.returncode != 0:
        print(f"\n❌  {script} failed. Fix errors above before continuing.")
        sys.exit(1)

print("\n" + "="*60)
print("  ✅  PIPELINE COMPLETE")
print("="*60)
print("\n  Outputs generated:")
for root, dirs, files in os.walk("outputs"):
    for f in files:
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        print(f"    {path}  ({size/1024:.1f} KB)")

print("\n  SQL queries: sql/03_segmentation_queries.sql")
print("  Run in PostgreSQL / BigQuery / Snowflake against your rfm_features table.")
print("="*60)
