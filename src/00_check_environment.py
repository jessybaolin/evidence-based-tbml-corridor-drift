"""
WHAT IT DOES:
  Tries to import each library the pipeline depends on (pandas, numpy, scikit-learn,
  xgboost, shap, matplotlib, weasyprint, graphviz, etc.), records each package's version,
  and writes a small JSON report. If any import fails it exits non-zero so the run stops
  early with a clear message instead of crashing deep inside a later step.

READS (inputs):
  - none (it only inspects the installed Python environment)

WRITES (outputs):
  - data/outputs/environment_check.json — per-package pass/fail + versions, Python info, overall status

EXIT CODE: 0 if all imports succeed, 1 (SystemExit) if any package is missing.
"""
from __future__ import annotations

import importlib  # lets us import modules by name from the REQUIRED list at runtime
import json
import sys

from tbml_common import DATA_OUTPUTS, ensure_dirs, utc_now, write_json

# Every third-party package the pipeline needs. Note import names differ from pip names
# in a couple of cases (e.g. "sklearn" not "scikit-learn", "yaml" not "pyyaml", "PIL" not "pillow").
REQUIRED = [
    "pandas", "pyarrow", "openpyxl", "numpy", "sklearn", "xgboost", "shap",
    "matplotlib", "yaml", "tabulate", "jinja2", "pygments", "weasyprint", "pypdf", "PIL", "joblib", "graphviz"
]


def main() -> None:
    ensure_dirs()

    # ---- Try to import each required package, one at a time ----
    checks = []
    for module in REQUIRED:
        try:
            # Import by name; record the version if the module exposes one.
            imported = importlib.import_module(module)
            version = getattr(imported, "__version__", "unknown")
            checks.append({"module": module, "status": "pass", "version": version})
        except Exception as exc:
            # Don't stop on the first failure — collect them all so the user sees
            # the complete list of what is missing in one go.
            checks.append({"module": module, "status": "fail", "error": str(exc)})

    # ---- Roll the per-package results up into one overall status ----
    status = "pass" if all(row["status"] == "pass" for row in checks) else "fail"
    report = {
        "generated_at": utc_now(),            # timestamp of this check
        "python_version": sys.version,        # which Python interpreter ran it
        "python_executable": sys.executable,  # full path to that interpreter (useful for venv debugging)
        "checks": checks,
        "status": status,
    }

    # ---- Save + print the report ----
    write_json(DATA_OUTPUTS / "environment_check.json", report)
    print(json.dumps(report, indent=2))

    # Fail loudly so 11_run_all.py halts the whole pipeline if a dependency is absent.
    if status != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
