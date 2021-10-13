# Compass

Metrics and dashboards to guide our engineering

setup
```
brew install poetry
poetry install
```

run
```
# PR age prometheus exporter
poetry run python compass/server.py

# Release handler
poetry run kopf run -A compass/k8s_handlers.py
```
---
kubernetes operator development in python
https://github.com/nolar/kopf https://codeberg.org/hjacobs/pytest-kind
https://srcco.de/posts/kubernetes-and-python.html
https://medium.com/swlh/building-a-kubernetes-operator-in-python-with-zalandos-kopf-37c311d8edff

setup
kubectl apply -f https://github.com/nolar/kopf/raw/main/peering.yaml

Run