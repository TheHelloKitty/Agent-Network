import os
import json
import requests
import subprocess
import sys

# Ensure cdp-sdk is installed and available
CDP_AVAILABLE = False
try:
    from cdp import Cdp, Wallet
    CDP_AVAILABLE = True
except ImportError:
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "cdp-sdk"])
        from cdp import Cdp, Wallet
        CDP_AVAILABLE = True
    except Exception:
        CDP_AVAILABLE = False

try:
    from upload_post import UploadPostClient
except ImportError:
    UploadPostClient = None
