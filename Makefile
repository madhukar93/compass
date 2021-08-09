compose_up:
	docker-compose -f docker/docker-compose.yml up -d

compose_down:
	docker-compose -f docker/docker-compose.yml down

docker-build-development:
	docker build -f docker/Dockerfile . -t compass-image --target development

docker-build-production:
	docker build -f docker/Dockerfile . -t compass-image --target production

development: compose_down docker-build-development compose_up
production: compose_down docker-build-production compose_up

apply-dashboard:
	kubectl -n monitoring create cm dashboard-compass --from-file=dashboards/dashboard_pr_age.json --dry-run=client -o yaml | kubectl apply -f -
	kubectl -n monitoring label --overwrite=true cm dashboard-compass grafana-dashboard=1
