import os
import shutil

def cleanup_temporary_files(*dirs):
    """Deletes temporary degraded clips and query frames."""
    for d in dirs:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Cleaned up temporary directory: {d}")
