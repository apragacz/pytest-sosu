SHELL := /bin/bash

PACKAGE_DIR := pytest_sosu
TESTS_DIR := tests
DIST_DIR := dist
BUILD_DIR := build

GREP := grep
AWK := awk
SORT := sort
RM := rm
FIND := find
XARGS := xargs
CAT := cat

PYTHON := python
FLAKE8 := flake8
FLAKE8_OPTS :=
BLACK := black
BLACK_OPTS :=
BLACK_CHECK_OPTS := --check --diff
BLACK_ARGS := ${PACKAGE_DIR} ${TESTS_DIR} ${ARGS}
MYPY := mypy
MYPY_OPTS :=
PYLINT := pylint
PYLINT_OPTS := --rcfile=setup.cfg
PYTEST := pytest
PYTEST_MODULE := pytest
PYTEST_OPTS := --failed-first --maxfail 5 --durations=10 -v
PYTEST_UNIT_OPTS := ${PYTEST_OPTS}
PYTEST_INTEGRATION_OPTS := ${PYTEST_OPTS}
PYTEST_UNIT_ARGS := tests/unit/ ${ARGS}
PYTEST_INTEGRATION_ARGS := tests/integration/ ${ARGS}
TWINE := twine
PIP_COMPILE := pip-compile
PIP_COMPILE_OPTS := --upgrade
COVERAGE := coverage
COVERAGE_RUN_OPTS := --source ${PACKAGE_DIR} --module ${PYTEST_MODULE}

.PHONY: help
help: ## Display this help screen
	@grep -E '^[\.a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: all
all: check test build check_package  ## check code, test, build, check package

.PHONY: install_dev
install_dev:  ## install all pip requirements and the package as editable
	${PYTHON} -m pip install -r requirements/requirements-dev.lock.txt ${ARGS}
	${PYTHON} -m pip install -e .

.PHONY: install_test
install_test:  ## install all pip requirements needed for testing and the package as editable
	${PYTHON} -m pip install -r requirements/requirements-test.lock.txt ${ARGS}
	${PYTHON} -m pip install -e .

.PHONY: upgrade_requirements
upgrade_requirements:  ## upgrade pip requirements lock files
	${PIP_COMPILE} ${PIP_COMPILE_OPTS} --output-file=requirements/requirements-base.lock.txt
	${PIP_COMPILE} ${PIP_COMPILE_OPTS} --output-file=requirements/requirements-test.lock.txt requirements/requirements-base.lock.txt requirements/requirements-test.in
	${PIP_COMPILE} ${PIP_COMPILE_OPTS} --output-file=requirements/requirements-dev.lock.txt requirements/requirements-test.lock.txt requirements/requirements-dev.in

.PHONY: test
test: test_unit test_integration  ## run tests

.PHONY: test_unit
test_unit:  ## run unit tests
	${PYTEST} ${PYTEST_UNIT_OPTS} ${PYTEST_UNIT_ARGS}

.PHONY: test_unit_cov
test_unit_cov:  ## run unit tests
	${COVERAGE} run ${COVERAGE_RUN_OPTS} ${PYTEST_UNIT_OPTS} ${PYTEST_UNIT_ARGS}

.PHONY: test_integration
test_integration:  ## run integration tests
	${PYTEST} ${PYTEST_INTEGRATION_OPTS} ${PYTEST_INTEGRATION_ARGS}

.PHONY: check
check: flake8 check_black mypy pylint  ## run all code checks

.PHONY: flake8
flake8:  ## run flake8
	${FLAKE8} ${FLAKE8_OPTS} ${ARGS}

.PHONY: check_black
check_black:  ## run black check
	${BLACK} ${BLACK_CHECK_OPTS} ${BLACK_ARGS}

.PHONY: mypy
mypy:  ## run mypy
	${MYPY} ${MYPY_OPTS} ${PACKAGE_DIR} ${ARGS}

.PHONY: pylint
pylint:  ## run pylint
# run pylint for production code and test code separately
	${PYLINT} ${PYLINT_OPTS} ${PACKAGE_DIR} ./*.py ${ARGS}
	${PYLINT} ${PYLINT_OPTS} --disable=duplicate-code --disable=redefined-outer-name --disable=too-many-arguments ${TESTS_DIR} ${ARGS}

.PHONY: upload_package
upload_package: build_package check_package  ## upload the package to PyPI
	${TWINE} upload ${DIST_DIR}/*

.PHONY: check_package
check_package: build_package  ## check that the built package is well-formed
	${TWINE} check ${DIST_DIR}/*

.PHONY: black
black:  ## run black
	${BLACK} ${BLACK_OPTS} ${BLACK_ARGS}

.PHONY: build
build: build_package  ## alias for build_package

.PHONY: build_package
build_package:  ## build package (source + wheel)
	-${RM} -r ${DIST_DIR}
	${PYTHON} setup.py sdist
	${PYTHON} setup.py bdist_wheel

.PHONY: clean
clean:  ## remove generated files
	-${RM} -r .tox
	-${RM} -r .pytest_cache
	-${RM} -r .mypy_cache

	${FIND} "." -iname '__pycache__' -type d -print0 | ${XARGS} -0 ${RM} -r

	-${RM} TEST-*.xml

	-${RM} .coverage
	-${RM} coverage.xml
	-${RM} -r coverage_html_report

	-${RM} -r ${DIST_DIR}
	-${RM} -r ${BUILD_DIR}
