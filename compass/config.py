"Read environment variables and store them"

import os
import sys
import logging

try:
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
    GITHUB_ORG_NAME = os.environ['GITHUB_ORG_NAME']

except KeyError:
    # TODO:Print missing key only
    logging.error("GITHUB_TOKEN or GITHUB_ORG_NAME missing (Hint : set env-variable)")
    sys.exit()
