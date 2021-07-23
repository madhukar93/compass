"Compass Server exposing metrics"

import pr_age
import config as c
import logging
from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server

if __name__ == "__main__":
    app = make_wsgi_app()

    pr_age.run(c.GITHUB_TOKEN, c.GITHUB_ORG_NAME)

    logging.info("starting server, PORT: 8000")
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
