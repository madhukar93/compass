"""
Index releases into Elasticsearch. This is triggered by deployment(rollout) updates.
"""
import arrow

import kopf
import sentry_sdk

from es_models import Change, FlattenedReleaseDoc
from github_utils import org

# TODO:
# - only run login via client to save startup time and avoid error logs? that might work only in dev mode
# - asyncio pl0x


@kopf.on.update("deployments", backoff=3600)
@kopf.on.update("rollouts", backoff=3600)
def deployment_diff_handler(body, old, new, logger, **kwargs):
    """
    Notify about the deployment update.
    Right now only creating release documents in Elasticsearch.
    """
    sentry_sdk.add_breadcrumb(
        message="running deployment_diff_handler for {body['metadata']['namespace']}/{body['kind']}/{body['metadata']['name']}",
        level="info",
    )
    try:
        change = Change(
            arrow.utcnow().datetime,
            old,
            new,
            org,
        )
        release_doc = FlattenedReleaseDoc.create(
            change=change,
            deployment=body,
            logger=logger,
        )
        release_doc.full_clean()
        release_doc.save()
    except ValueError as e:
        raise kopf.PermanentError(f"release not created - {e}")
