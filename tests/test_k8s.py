import pykube
import yaml
from tenacity import Retrying, RetryError, stop_after_attempt, wait_fixed

deployment_yaml = """---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-deployment
  labels:
    app: test-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: test-app
  template:
    metadata:
      labels:
        app: test-app
    spec:
      containers:
      - name: test-container
        image: busybox:latest
        command: ["sleep", "3600"]
"""


def test_replicaset_creation_handler(kind_cluster):
    """test what happens when a replicaset is created"""
    deployment_spec = yaml.safe_load(deployment_yaml)
    pykube.Deployment(kind_cluster.api, deployment_spec).create()
    for attempt in Retrying(stop=stop_after_attempt(10), wait=wait_fixed(2)):
        with attempt:
            print("checking if deployment exists")
            assert pykube.Deployment(kind_cluster.api, deployment_spec).exists()
