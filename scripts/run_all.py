# -*- coding: utf-8 -*-
"""Orchestrateur : régénère tout le projet de bout en bout.

Étapes :
  1. Génère les données brutes        (scripts/generate_data.py)
  2. (Re)construit les notebooks       (scripts/_build_notebooks.py)
  3. Exécute les 3 notebooks            -> data/processed, reports/figures, models

Usage :
  .venv\\Scripts\\python scripts\\run_all.py
"""
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
NB_DIR = os.path.join(BASE, "notebooks")
NOTEBOOKS = [
    "01_nettoyage_preparation.ipynb",
    "02_analyse_exploratoire.ipynb",
    "03_prevision_forecasting.ipynb",
]


def run(cmd, cwd=BASE):
    print("\n>>", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def main():
    run([PY, os.path.join("scripts", "generate_data.py")])
    run([PY, os.path.join("scripts", "_build_notebooks.py")])
    for nb in NOTEBOOKS:
        run([PY, "-m", "jupyter", "nbconvert", "--to", "notebook",
             "--execute", "--inplace",
             "--ExecutePreprocessor.timeout=600", nb], cwd=NB_DIR)
    print("\n✅ Pipeline terminé : data/processed, reports/figures et models à jour.")


if __name__ == "__main__":
    main()
