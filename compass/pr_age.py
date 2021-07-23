"All class definitions"

import os
import datetime
import constants as c
from github import Github
from prometheus_client import Gauge

# pylint: disable=R0201
class Pr_Age():
    "Put all PR Age metrics related stuffs"

    def __init__(self):
        self.pr_gauge = self.get_pr_age_obj()

    def get_pr_age_obj(self):
        "create and return Gauge object"
        return Gauge('pr_age', 'PR Age matrics', ['repo_name', 'pr_id', 'state'])

    def calc_pr_age(self, created_at, state, closed_at):
        "calculates Age of open/closed PR - Currently wrt Minutes"

        # created_at = datetime.datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")

        if state == 'open':
            now = datetime.datetime.now()
            pr_age = now - created_at
            pr_age_time = pr_age.total_seconds() / 60

        elif state == 'closed':
            # closed_at = datetime.datetime.strptime(closed_at, "%Y-%m-%dT%H:%M:%SZ")
            pr_age = closed_at - created_at
            pr_age_time = pr_age.total_seconds() / 60

        return pr_age_time


    def make_metric(self, repo, pr):
        "with some labels, set pr's age in gauge metric"
        pr_age = self.calc_pr_age(pr.created_at, pr.state, pr.closed_at)
        self.pr_gauge.labels(repo.name, pr.id, pr.state).set(pr_age)

    def run(self):
        "Using Github api to fetch data and then create metric"

        git = Github(c.GITHUB_TOKEN)
        org = git.get_organization(c.GITHUB_ORG_NAME)

        repos = org.get_repos()
        for repo in repos:
            prs = repo.get_pulls("all")

            for pr in prs:
                self.make_metric(repo, pr)
