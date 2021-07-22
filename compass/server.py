from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server

if __name__ == "__main__":
    app = make_wsgi_app()
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
