.PHONY: all deploy pypi-info authors clean test

all: deploy clean

deploy:
	python setup.py sdist upload

pypi-info:
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
	rm -f test_report.txt
	rm -f *.log
	rm -f *.pyc
	rm -f saltobserver/*.pyc
	rm -f scripts/*.pyc

test:
	nosetests --with-coverage --cover-package=saltobserver --with-tissue --tissue-ignore=E501 --tissue-fail-on-error 3>&1 1>&2 2>&3 | tee test_report.txt
