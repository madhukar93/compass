"""
github client and utils
"""
import config
from github import Github

github_client = Github(config.GITHUB_TOKEN)
org = github_client.get_organization(config.GITHUB_ORG_NAME)
