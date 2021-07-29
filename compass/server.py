"Compass Server"

import pr_age
import logging
from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server


def app(environ, start_response):
    "application to serve metrics"
    pr_age.run()
    wsgi_app = make_wsgi_app()
    return wsgi_app(environ, start_response)


if __name__ == "__main__":
    logging.info("starting server, PORT: 8000")
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
