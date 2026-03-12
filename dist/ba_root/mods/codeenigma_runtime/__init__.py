import platform
import sys
import rich

if platform.system() != 'Linux':
    rich.print("codeenigma_runtime was compiled for 'Linux'. You are on a different OS.")
    sys.exit(1)

from .codeenigma_runtime import execute_secure_code
