.PHONY: install add black black/check isort isort/check mypy lint lint/check test run

install:
	pip install -r requirements.txt

add:
	pip install "$(package)"
	pip freeze | grep "$(package)" >> requirements.txt
	sort -u -o requirements.txt requirements.txt

black:
	black demo

black/check:
	black --check --diff demo

isort:
	isort demo

isort/check:
	isort --check --diff demo

pylint:
	pylint demo

lint: isort black

lint/check: isort/check black/check pylint

mypy:
	mypy demo

test:
	DEMO_env=test pytest $(o)

run:
	python -m demo
