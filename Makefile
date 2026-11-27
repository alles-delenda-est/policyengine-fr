all: install format test build

documentation:
	jupyter-book clean docs
	jupyter-book build docs

format:
	ruff format .
	ruff check .

check-docs:
	python bin/check_doc_currency.py

install:
	pip install -e .[dev]

test:
	policyengine-core test -c policyengine_fr policyengine_fr/tests
	pytest tests/ -q

build:
	python -m build

ui-install:
	cd ui && npm install

ui-build:
	cd ui && npm run build

ui-test:
	cd ui && npm run lint && npm test

studio:
	python -m policyengine_fr.studio --open

changelog:
	towncrier build --yes --version $$(python -c "import re; print(re.search(r'version = \"(.+?)\"', open('pyproject.toml').read()).group(1))")
