"""
smoke_test.py — stub file to avoid pytest collection running the smoke script.

Use `python smoke_runner.py` to run the smoke checks manually.
"""


if __name__ == "__main__":
      import subprocess
      import sys
      subprocess.run([sys.executable, "smoke_runner.py"] + sys.argv[1:])
