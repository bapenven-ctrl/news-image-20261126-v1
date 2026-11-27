#!/usr/bin/env python3
"""Copy entry.png to the output directory (make.fun program entrypoint).

Standard library only, no network. The judge runs this with
MAKEFUN_OUTPUT_DIR set to a writable folder; the program writes
entry.png there and exits 0.
"""
import os
import shutil
import sys

ENTRY = "entry.png"


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "output")
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), ENTRY)
    if not os.path.isfile(src):
        print(f"error: {ENTRY} is missing next to main.py; "
              "the repository must ship entry.png", file=sys.stderr)
        sys.exit(1)
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(src, os.path.join(out_dir, ENTRY))


if __name__ == "__main__":
    main()
