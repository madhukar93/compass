from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server
from pr_age import Pr_Age

if __name__ == "__main__":
    app = make_wsgi_app()

    age_pr = Pr_Age()
    age_pr.run()

    print("starting server, PORT: 8000")
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
