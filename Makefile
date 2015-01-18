.PHONY: all deploy pypi-info authors clean

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
	rm -f *.log
	rm -f *.pyc
	rm -f saltobserver/*.pyc

test:
	nosetests --with-coverage --cover-package=saltobserver
