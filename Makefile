.PHONY: all pypirc deploy pypi-info authors clean test

all: clean

pypirc:
	@if test "$(PYPI_CREDENTIALS)" != ""; then \
	    echo "generating ~/.pypirc"; \
	    echo "[distutils]" > ~/.pypirc; \
	    echo "index-servers = pypi" >> ~/.pypirc; \
	    echo "[pypi]" >> ~/.pypirc; \
	    echo "repository: https://pypi.python.org/pypi" >> ~/.pypirc; \
	    echo -n "username: " >> ~/.pypirc; \
	    echo $(PYPI_CREDENTIALS) | cut -d ':' -f 1 >> ~/.pypirc; \
	    echo -n "password: " >> ~/.pypirc; \
	    echo $(PYPI_CREDENTIALS) | cut -d ':' -f 2 >> ~/.pypirc; \
	fi

deploy: pypirc
	python setup.py sdist upload

pypi-info: pypirc
	python setup.py register

authors:
	@echo "Saltobserver is maintained by Daniel Nägele <code@danieln.de>." > AUTHORS
	@echo "Contributions by:" >> AUTHORS
	@git log --raw | grep "^Author: " | sort | \
		awk '!/@users.noreply.github.com/' | uniq -c | \
		grep -v 'Nägele' | sort -n -r | cut -d ':' -f 2 >> AUTHORS
	@echo "" >> AUTHORS
	@echo "See also:" >> AUTHORS
	@echo "https://github.com/analogbyte/saltobserver/graphs/contributors" >> AUTHORS

clean:
	rm -rf saltobserver.egg-info/
	rm -rf dist/
	rm -f dump.rdb
	rm -f *.log
	rm -f *.pyc
	rm -f saltobserver/*.pyc
	rm -f scripts/*.pyc

# test requires the following pypi packages: nose coverage tissue
test:
	nosetests --with-coverage --cover-package=saltobserver --with-tissue --tissue-ignore=E501 --tissue-fail-on-error
