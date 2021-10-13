"caclulate PR related metrics and expose them as prometheus metrics"

import datetime
import logging
from wsgiref.simple_server import make_server

from github_utils import github_client
from prometheus_client import Gauge, make_wsgi_app

import config

# TODO: how to add prefix to all metrics in the project
pr_gauge = Gauge(
    "compass_pr_age",
    "PR Age metrics",
    ["repo_name", "pr_id"],
)


def calculate_pr_age(created_at):
    now = datetime.datetime.now()
    pr_age = now - created_at
    pr_age_time = pr_age.total_seconds()
    return pr_age_time


def make_metric(repo, pr):
    "with some labels, set pr's age in gauge metric"

    pr_age = calculate_pr_age(pr.created_at)
    pr_gauge.labels(repo.name, pr.id).set(pr_age)


def run():
    "Using Github api to info and then create metric"

    org = github_client.get_organization(config.GITHUB_ORG_NAME)

    # To eleminate closed PRs and deleted repos
    pr_gauge.clear()

    repos = org.get_repos()
    for repo in repos:
        prs = repo.get_pulls("open")

        for pr in prs:
            make_metric(repo, pr)


def app(environ, start_response):
    "application to serve metrics"
    run()
    wsgi_app = make_wsgi_app()
    return wsgi_app(environ, start_response)


if __name__ == "__main__":
    logging.info("starting server, PORT: 8000")
    httpd = make_server("", 8000, app)
    httpd.serve_forever()
