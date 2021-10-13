import logging
import os
import sys

import sentry_sdk

try:
    GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
    GITHUB_ORG_NAME = os.environ["GITHUB_ORG_NAME"]
    ENVIRONMENT = os.environ["ENV"]
    ES_URL = os.environ["ES_URL"]
    SENTRY_DSN = os.environ["SENTRY_DSN"]

except KeyError as e:
    logging.error(f"{e} env var not set")
    sys.exit()

sentry_sdk.init(
    dsn=SENTRY_DSN,
    environment=ENVIRONMENT,
    attach_stacktrace=True,
    # https://sentry.io/organizations/beecash/issues/2680932914/?environment=local&project=5983889&query=&statsPeriod=14d
    ignore_errors=["DefaultCredentialsError", "InvalidStateError"],
)
