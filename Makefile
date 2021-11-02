VIRTUALENV = virtualenv --python=python3
VENV := $(shell echo $${VIRTUAL_ENV-.venv})
PYTHON = $(VENV)/bin/python
TOX = $(VENV)/bin/tox
TEMPDIR := $(shell mktemp -du)
NAME=kinto_changes

build-requirements:
	$(VIRTUALENV) $(TEMPDIR)
	$(TEMPDIR)/bin/pip install -U pip
	$(TEMPDIR)/bin/pip install -Ue .
	$(TEMPDIR)/bin/pip freeze | grep -v -- '-e' > requirements.txt

virtualenv: $(PYTHON)
$(PYTHON):
	virtualenv $(VENV)

tox: $(TOX)
$(TOX): virtualenv
	$(VENV)/bin/pip install tox

tests-once: tox
	$(VENV)/bin/tox -e py38

tests: tox
	$(VENV)/bin/tox

format:
	isort --profile=black --lines-after-imports=2 tests $(NAME)
	black tests $(NAME)
