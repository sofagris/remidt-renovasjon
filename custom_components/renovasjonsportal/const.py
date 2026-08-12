"""Constants for the Renovasjonsportal integration."""

from datetime import timedelta

DOMAIN = "renovasjonsportal"
PLATFORMS = ["sensor"]

API_BASE_URL = "https://kalender.renovasjonsportal.no/api"
WEB_URL = "https://kalender.renovasjonsportal.no/"
REQUEST_TIMEOUT = 15
UPDATE_INTERVAL = timedelta(hours=12)

CONF_ADDRESS_ID = "address_id"
CONF_ADDRESS_NAME = "address_name"
CONF_MUNICIPALITY = "municipality"

