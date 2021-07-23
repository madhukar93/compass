"Read environment variables and store them"

import os
import sys
import logging

# for Testing. will be removed
# os.environ['GITHUB_TOKEN'] = '...GITHUB_API_ACCESS_TOKEN...'
# os.environ['GITHUB_ORG_NAME'] = '...eg:bukukasio...'

try:
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
    GITHUB_ORG_NAME = os.environ['GITHUB_ORG_NAME']

except KeyError:
    logging.error("GITHUB_TOKEN or GITHUB_ORG_NAME missing (Hint : set env-variable)")
    sys.exit()
