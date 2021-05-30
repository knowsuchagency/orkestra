.PHONY: bootstrap

PYTHON_VERSION ?= 3.8.10

bootstrap:
	PYTHON_VERSION=${PYTHON_VERSION} bash scripts/bootstrap.sh
