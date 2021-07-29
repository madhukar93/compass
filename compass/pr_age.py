"PR age metric codes"

import os
import datetime
import config as c
from github import Github
from prometheus_client import Gauge

def get_pr_age_obj():
    "return Gauge object"
    return Gauge('pr_age', 'PR Age matrics', ['repo_name', 'pr_id'])


pr_gauge = get_pr_age_obj()

def calc_pr_age(created_at):
    "calculates Age of open/closed PR - Currently wrt Seconds"

    now = datetime.datetime.now()
    pr_age = now - created_at
    pr_age_time = pr_age.total_seconds()
    return pr_age_time


def make_metric(repo, pr):
    "with some labels, set pr's age in gauge metric"

    pr_age = calc_pr_age(pr.created_at)
    pr_gauge.labels(repo.name, pr.id).set(pr_age)


def run():
    "Using Github api to fetch data and then create metric"

    git = Github(c.GITHUB_TOKEN)
    org = git.get_organization(c.GITHUB_ORG_NAME)

    repos = org.get_repos()
    for repo in repos:
        prs = repo.get_pulls("open")

        for pr in prs:
            make_metric(repo, pr)
