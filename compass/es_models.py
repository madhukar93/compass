"""
TODO:
set up ILM policy
https://www.elastic.co/guide/en/elasticsearch/reference/current/use-elasticsearch-for-time-series-data.html
"""
import logging
from datetime import datetime

import arrow
import sentry_sdk
from elasticsearch_dsl import Date, Document, Integer, Keyword, Text, connections
from elasticsearch_dsl.document import InnerDoc
from elasticsearch_dsl.field import Nested
from github import Commit, Organization, PullRequest, Repository

import config

INDEX_NAME = "compass-v1"
es_hosts = [config.ES_URL]
connections.create_connection(hosts=es_hosts)


class ChangeStatsDoc(InnerDoc):
    additions = Integer()
    deletions = Integer()
    total = Integer()

    # TODO: try using __new__, since we can't mess with __init__
    @classmethod
    def create(cls, stats, *args, **kwargs):
        try:
            # Commit
            total = stats.total
        except AttributeError:
            # PullRequest
            total = stats.additions + stats.deletions
        return cls(
            additions=stats.additions,
            deletions=stats.deletions,
            total=total,
            *args,
            **kwargs,
        )

    @classmethod
    def create_combined(cls, stats_list, *args, **kwargs):
        additions = sum(s.additions for s in stats_list)
        deletions = sum(s.deletions for s in stats_list)
        total = additions + deletions
        return cls(
            additions=additions,
            deletions=deletions,
            total=total,
            *args,
            **kwargs,
        )


class CommitDoc(InnerDoc):
    author = Keyword()
    message = Text()
    sha = Keyword()
    timestamp = Date()
    change_stats = Nested(ChangeStatsDoc)

    @classmethod
    def create(cls, commit: Commit.Commit, *args, **kwargs):
        return cls(
            author=commit.commit.author.email,
            message=commit.commit.message,
            sha=commit.sha,
            timestamp=arrow.get(commit.commit.author.date).datetime,
            change_stats=ChangeStatsDoc.create(commit.stats),
            *args,
            **kwargs,
        )


class FlattenedCommitDoc(InnerDoc):
    author = Keyword()
    message = Text()
    sha = Keyword()
    timestamp = Date()
    additions = Integer()
    deletions = Integer()
    total = Integer()

    @classmethod
    def create(cls, commit: Commit.Commit, *args, **kwargs):
        change_stats = ChangeStatsDoc.create(commit.stats)
        return cls(
            author=commit.commit.author.email,
            message=commit.commit.message,
            sha=commit.sha,
            timestamp=arrow.get(commit.commit.author.date).datetime,
            additions=change_stats.additions,
            deletions=change_stats.deletions,
            total=change_stats.total,
            *args,
            **kwargs,
        )


class PullRequestDoc(InnerDoc):
    author = Keyword()
    title = Text()
    html_url = Keyword()
    merged_at = Date()
    change_volume = Nested(ChangeStatsDoc)
    # use date range?
    age_seconds = Integer()

    @classmethod
    def create(cls, pull_request: PullRequest.PullRequest, *args, **kwargs):
        merged_at_utc = (
            pull_request.merged_at and arrow.get(pull_request.merged_at).datetime
        )
        return cls(
            author=pull_request.user.login,
            title=pull_request.title,
            html_url=pull_request.html_url,
            merged_at=pull_request.merged_at
            and arrow.get(
                pull_request.merged_at
            ).datetime,  # get tz aware ts if merged_at is not None
            change_volume=ChangeStatsDoc.create(pull_request),
            age_seconds=merged_at_utc
            and (
                merged_at_utc
                - arrow.get(
                    pull_request.get_commits()[0].commit.author.date
                ).datetime
            ).total_seconds(),
            *args,
            **kwargs,
        )


class ChangeDoc(InnerDoc):
    """
    Represents a build in Elasticsearch.
    """

    repo_url = Keyword()
    head_sha = Keyword()
    committed_at = Date()
    change_log = Nested(FlattenedCommitDoc)
    change_volume = Nested(ChangeStatsDoc)
    pull_request = Nested(PullRequestDoc)

    @classmethod
    def create(
        cls,
        repo: Repository.Repository,
        head_sha: str,
        base_sha: str,
        *args,
        **kwargs,
    ):
        head = repo.get_commit(sha=head_sha)
        pull_requests = head.get_pulls()  # type: ignore
        if pull_requests.totalCount > 1:
            pr_links = ", ".join([pr.html_url for pr in pull_requests])
            sentry_sdk.capture_message(
                f"{repo.name}: Multiple pull requests found for {head.html_url}: {pr_links}"
            )
        # we're not handling weird cases where pull requests haven't merged for a release
        # or there are multiple PRs with the same (merge)commit
        # the current way should work fine with merge, squash merge and rebase and merge
        pull_request_doc = None
        try:
            pull_request = pull_requests[0]
            pull_request_doc = PullRequestDoc.create(pull_request)
        except IndexError as e:
            sentry_sdk.capture_message(
                f"{repo.name}: no pull requests found for {head.html_url}"
            )
        commits_between_base_head = repo.compare(base=base_sha, head=head_sha).commits

        return cls(
            repo_url=repo.html_url,
            head_sha=head.sha,
            committed_at=arrow.get(head.commit.author.date).datetime,
            change_log=[
                FlattenedCommitDoc.create(commit)
                for commit in commits_between_base_head
            ],
            change_volume=ChangeStatsDoc.create_combined(
                [c.stats for c in commits_between_base_head]
            ),
            pull_request=pull_request_doc,
            *args,
            **kwargs,
        )


class k8sResource(InnerDoc):
    """
    this is how k8s forms a fqdn for a resource
    """

    namespace = Keyword()
    # version = Keyword()
    kind = Keyword()
    name = Keyword()

    @classmethod
    def create(cls, k8s_object: dict):
        return cls(
            namespace=k8s_object["metadata"]["namespace"],
            kind=k8s_object["kind"],
            name=k8s_object["metadata"]["name"],
        )


class Change:
    """
    information about the change for creating a release
    """

    def __init__(
        self,
        timestamp: datetime,
        old: dict,
        new: dict,
        org: Organization.Organization,
    ):
        old_deployment_meta = k8s_deployment_metadata(old)
        self.app: str = old_deployment_meta["app"]
        self.old_version: str = old_deployment_meta["version"]
        self.new_version: str = k8s_deployment_metadata(new)["version"]
        if self.old_version == self.new_version:
            raise ValueError(
                f"{self.app}: old and new versions are the same - {self.new_version}"
            )
        self.reason: str = (
            f"container image updated from {self.old_version} to {self.new_version}"
        )
        self.event_timestamp: datetime = timestamp
        self.part_of: Repository.Repository = org.get_repo(
            old_deployment_meta["part-of"]
        )


def k8s_deployment_metadata(deployment: dict) -> dict:
    """
    validate rules for app and version and return a dict with app and version

    deployment name MUST be unique in the cluster.
    deployment name MUST be equal to the app label
    'part-of' label MUST be a repo
    app label MUST match ONLY ONE of the containers in template.containers,
    henceforth referred to as ‘app container’
     - updating app container image -> release
    The app container’s image MUST match the annotation app.bukukas.io/version
    the app.bukukas.io/version must be a valid git ref
    """
    validation_errors = []
    try:
        app = deployment["metadata"]["labels"]["app"]
        assert bool(app)
    except AssertionError as e:
        validation_errors.append(f"metadata.labels.app missing")
    except KeyError as e:
        validation_errors.append(f"error with checking metadata.labels.app {e}")

    try:
        version_annotation = deployment["metadata"]["annotations"][
            "app.bukukas.io/version"
        ]
        try:
            app_image = None
            for container in deployment["spec"]["template"]["spec"]["containers"]:
                if container["name"] == app:
                    app_image = container["image"]
                    # the invalid state when there are multiple containers with the same name is validated by k8s

                    image_tag = app_image.split(":")[1]
                    assert version_annotation == image_tag
                    break

        except IndexError as e:
            validation_errors.append(
                f"error with checking image tag {container['name']}: image is {app_image}"
            )
        except KeyError as e:
            validation_errors.append(
                f"Error matching app label with container, missing key: {e}"
            )
        except AssertionError as e:
            validation_errors.append(
                f"metadata.annotations.app.bukukas.io/version != {image_tag}"
            )
    except KeyError as e:
        validation_errors.append(f"annotation app.bukukas.io/version missing")

    if validation_errors:
        raise ValueError(validation_errors)

    return {
        "app": app,
        "version": version_annotation,
        "part-of": deployment["metadata"]["labels"]["part-of"],
    }


class FlattenedReleaseDoc(Document):
    """
    Represents a release in Elasticsearch.
    """

    class Index:
        """
        Defines the Elasticsearch index and type.
        """

        name = INDEX_NAME
        # doc_type = "release"
        settings = {
            "number_of_shards": 5,
            "number_of_replicas": 1,
        }

    doc_type = "release"
    project_name = Keyword()
    app_name = Keyword()
    reason = Text()
    event_timestamp = Date()
    deployment_lead_time_seconds = Integer()

    # TODO: write function to auto flatten Object and Nested fields
    k8s_resource_namespace = Keyword()
    k8s_resource_kind = Keyword()
    k8s_resource_name = Keyword()

    change_repo_url = Keyword()
    change_head_sha = Keyword()
    change_committed_at = Date()
    change_volume_additions = Integer()
    change_volume_deletetions = Integer()
    change_volume_total = Integer()
    change_log = Nested(FlattenedCommitDoc)

    change_pull_request_html_url = Keyword()
    change_pull_request_author = Keyword()
    change_pull_request_title = Text()
    change_pull_request_additions = Integer()
    change_pull_request_deletions = Integer()
    change_pull_request_total = Integer()
    change_pull_request_age_seconds = Integer()

    @classmethod
    def create(cls, change: Change, deployment, logger):
        logger = logger or logging.getLogger()
        head_sha = change.new_version.rsplit("-")[-1]
        base_sha = change.old_version.rsplit("-")[-1]
        change_doc = ChangeDoc.create(
            repo=change.part_of, head_sha=head_sha, base_sha=base_sha
        )
        k8s_resource = k8sResource.create(deployment)
        pull_request_fields = {}
        if change_doc.pull_request:
            pull_request_fields = {
                "change_pull_request_html_url": change_doc.pull_request.html_url,
                "change_pull_request_author": change_doc.pull_request.author,
                "change_pull_request_title": change_doc.pull_request.title,
                "change_pull_request_additions": change_doc.pull_request.change_volume.additions,
                "change_pull_request_deletions": change_doc.pull_request.change_volume.deletions,
                "change_pull_request_total": change_doc.pull_request.change_volume.total,
                "change_pull_request_age_seconds": change_doc.pull_request.age_seconds,
            }
        return cls(
            # release
            project_name=change.part_of.name,
            app_name=change.app,
            reason=change.reason,
            event_timestamp=change.event_timestamp,
            deployment_lead_time_seconds=(
                change.event_timestamp - change_doc.committed_at
            ).total_seconds(),
            # k8s object reference
            k8s_resource_namespace=k8s_resource.namespace,
            k8s_resource_kind=k8s_resource.kind,
            k8s_resource_name=k8s_resource.name,
            # change from github
            change_repo_url=change_doc.repo_url,
            change_head_sha=change_doc.head_sha,
            change_committed_at=change_doc.committed_at,
            change_volume_additions=change_doc.change_volume.additions,
            change_volume_deletetions=change_doc.change_volume.deletions,
            change_volume_total=change_doc.change_volume.total,
            change_log=change_doc.change_log,
            **pull_request_fields,
        )


if __name__ == "__main__":
    FlattenedReleaseDoc.init()
