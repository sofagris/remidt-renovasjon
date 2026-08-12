"""Constants for the Renovasjonsportal integration."""

from datetime import timedelta
from pathlib import Path
import json

DOMAIN = "renovasjonsportal"
PLATFORMS = ["sensor"]

API_BASE_URL = "https://kalender.renovasjonsportal.no/api"
WEB_URL = "https://kalender.renovasjonsportal.no/"
REQUEST_TIMEOUT = 15
UPDATE_INTERVAL = timedelta(hours=12)

CONF_ADDRESS_ID = "address_id"
CONF_ADDRESS_NAME = "address_name"
CONF_MUNICIPALITY = "municipality"

URL_BASE = f"/{DOMAIN}"

with Path(__file__).with_name("manifest.json").open(encoding="utf-8") as manifest_file:
    INTEGRATION_VERSION = json.load(manifest_file).get("version", "0.0.0")
