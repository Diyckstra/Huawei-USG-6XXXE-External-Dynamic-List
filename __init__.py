import time
import ipaddress
import json
import datetime
from time import gmtime, strftime
from loguru import logger

RANGE_LIST = 1500
RESTRICTED_SERVER_CIPHERS  = "ALL"

logger.add("EDL.log", format="{time:HH:mm:ss DD.MM.YYYY} {level} {message}", rotation="100 MB")
