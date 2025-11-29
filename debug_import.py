import sys
import io

# Capture stdout
capture = io.StringIO()
original_stdout = sys.stdout
sys.stdout = capture

try:
    import shinzo
    from shinzo.instrumentation import instrument_server
    import repro
except Exception as e:
    sys.stderr.write(f"Import failed: {e}\n")

sys.stdout = original_stdout
output = capture.getvalue()

if output:
    sys.stderr.write(f"STDOUT POLLUTION DETECTED:\n{repr(output)}\n")
    sys.exit(1)
else:
    sys.stderr.write("No stdout pollution detected during import.\n")
    sys.exit(0)
