#!/usr/bin/env python3
import glob
import os
import sys

OLD = "np.clip(x, a_min=-88)"
NEW = "np.clip(x, -88)"

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROJECTS = ["evotune", "evotune_ESM", "fittop", "mutation"]


def find_activations(project):
    venv = os.path.join(REPO_ROOT, "projects", project, ".venv")
    if not os.path.isdir(venv):
        return None
    hits = glob.glob(
        os.path.join(venv, "**", "jax_unirep", "activations.py"), recursive=True
    )
    return hits[0] if hits else None


def patch(path):
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    if OLD not in src:
        if NEW in src:
            print(f"  already patched: {path}")
        else:
            print(f"  ERROR target line not found, not touching: {path}")
        return
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(src.replace(OLD, NEW))
    print(f"  patched: {path}")


def main(argv):
    if argv:
        targets = argv
    else:
        targets = []
        for project in PROJECTS:
            path = find_activations(project)
            if path is None:
                print(f"  skip {project}: no .venv or jax_unirep not installed")
            else:
                targets.append(path)
    if not targets:
        print("nothing to patch")
        return 0
    for path in targets:
        patch(path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
