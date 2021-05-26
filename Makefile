.PHONY: bootstrap

PYTHON_VERSION ?= 3.9.5

bootstrap:
	PYTHON_VERSION=${PYTHON_VERSION} bash scripts/bootstrap.sh
