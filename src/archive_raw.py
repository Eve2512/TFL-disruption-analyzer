import requests
import gzip
from datetime import datetime, timezone
from pathlib import Path 

STATUS_URL = "https://api.tfl.gov.uk/Line/Mode/tube/Status"
TIMEOUT = 10

now = datetime.now(timezone.utc)
repo_root = Path()
