"""Shared body of the stub runners used by the `review-override.py evidence`
tests. Each stub names one runner and passes its MODES table here.

Environment:
  STUB_MODE   key into MODES (default `fail`): the output to print and the
              exit code to return
  STUB_ARGV   file that gets one JSON line with argv[1:] per call
  STUB_WRITE  repo-relative file to append a line to before printing
              (a runner that mutates the tree)
  STUB_SLEEP  seconds: start a child that sleeps as long, write its pid to
              `$STUB_ARGV.child`, then sleep (a runner that hangs)
"""

import json
import os
import subprocess
import sys
import time


def run(modes):
    record = os.environ.get("STUB_ARGV")
    if record:
        with open(record, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(sys.argv[1:]) + "\n")
    target = os.environ.get("STUB_WRITE")
    if target:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("# edited by a stub runner\n")
    seconds = float(os.environ.get("STUB_SLEEP") or 0)
    if seconds:
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(%r)" % seconds])
        if record:
            with open(record + ".child", "w", encoding="utf-8") as handle:
                handle.write(str(child.pid))
        time.sleep(seconds)
    mode = os.environ.get("STUB_MODE", "fail")
    if mode not in modes:
        sys.stderr.write("stub: unknown STUB_MODE %s\n" % mode)
        return 99
    code, text = modes[mode]
    sys.stdout.write(text.replace("{cwd}", os.getcwd()))
    return code
