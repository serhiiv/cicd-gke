# cicd-gke
Setup GitHub Actions CI/CD workflow to implement single-service blue/green deployment to any cloud-hosted Kubernetes cluster GKE.



## Deploy

Build image

`docker build -t serhii714/ds:iter3 .`

Start 

`docker container prune --force && docker compose -d`

Set dalay for rl-slave-1

`docker exec rl-slave-1 tc qdisc add dev eth0 root netem delay 300ms`

Remove dalay for rl-slave-1

`docker exec rl-slave-1 tc qdisc del dev eth0 root`

Stop

`docker compose down`

## Develop

Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U -r dev_requirements.txt 
```

Report coverage by tests

`python -m pytest --cov-report term-missing --cov=app tests/`

Pytest

`python -m pytest -v --cache-clear`

Start in debug mode

`docker container prune --force && docker compose -f dev_compose.yaml up`

Stop

`docker compose down`
