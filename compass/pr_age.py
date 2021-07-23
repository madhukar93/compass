"All class definitions"

import os
import datetime
from github import Github
from prometheus_client import Gauge

def get_pr_age_obj():
    "create and return Gauge object"
    return Gauge('pr_age', 'PR Age matrics', ['repo_name', 'pr_id', 'state'])


pr_gauge = get_pr_age_obj()

def calc_pr_age(created_at, state, closed_at):
    "calculates Age of open/closed PR - Currently wrt Minutes"

    if state == 'open':
        now = datetime.datetime.now()
        pr_age = now - created_at
        pr_age_time = pr_age.total_seconds() / 60

    elif state == 'closed':
        pr_age = closed_at - created_at
        pr_age_time = pr_age.total_seconds() / 60

    return pr_age_time


def make_metric(repo, pr):
    "with some labels, set pr's age in gauge metric"
    pr_age = calc_pr_age(pr.created_at, pr.state, pr.closed_at)
    pr_gauge.labels(repo.name, pr.id, pr.state).set(pr_age)

def run(GITHUB_TOKEN, GITHUB_ORG_NAME):
    "Using Github api to fetch data and then create metric"

    git = Github(GITHUB_TOKEN)
    org = git.get_organization(GITHUB_ORG_NAME)

    repos = org.get_repos()
    for repo in repos:
        prs = repo.get_pulls("all")

        for pr in prs:
            make_metric(repo, pr)
