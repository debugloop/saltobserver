Salt Observer
=============

This is a simple webapp for presenting data as offered by `Salt's Redis
Returner`_ written in `Flask`_. A static demo is available `here`_.

.. _`Salt's Redis Returner`: https://github.com/saltstack/salt/blob/develop/salt/returners/redis_return.py
.. _`Flask`: http://flask.pocoo.org/
.. _`here`: http://analogbyte.github.io/saltobserver/

.. image:: http://files.danieln.de/public/saltobserver.png
   :alt: Screenshot of Saltobserver (17-12-2014)
   :width: 1000 px
   :target: http://files.danieln.de/public/saltobserver.png

Features
~~~~~~~~

- a simple and responsive interface
- three main views:
    * a function view showing all minions that ran a particular function (as
      shown on the screenshot)
    * a history view for looking at a minion's history with a specific function
    * a job view listing all minions which ran a specific job
- a customizable navbar, which links to function views
- searchpages for everything
- live updates for the function view using websockets and `Redis' Keyspace Notifications`_
- a collapsible representation of raw job data using the awesome `renderjson`_

.. _`Redis' Keyspace Notifications`: http://redis.io/topics/notifications
.. _`renderjson`: https://github.com/caldwell/renderjson

Running it from PyPI
~~~~~~~~~~~~~~~~~~~~

Just install it using ``pip install saltobserver``. As always, it is
recommended to do so in a virtualenv. After that, the command
``run_saltobserver`` will be available within this virtualenv. If you want to
use non-default settings (at least look at the `defaults`_) prefix the command
with ``export SALTOBSERVER_SETTINGS=/path/to/config``. Other than that, you may
pass gunicorn options to the ``run_saltobserver`` command, they will be passed
on so that you can configure gunicorn for use with a proxy server.

.. _`defaults`: https://raw.githubusercontent.com/analogbyte/saltobserver/master/saltobserver/config.py

A typical deployment could use this command with supervisord:

.. code::
  export SALTOBSERVER_SETTINGS=/home/saltobserver/config.cfg run_saltobserver --log-file=/var/log/saltobserver/gunicorn.log

Running it from Source
~~~~~~~~~~~~~~~~~~~~~~

If your minions return their data to some Redis instance, it is as
simple as cloning this repo running ``scripts/run_saltobserver`` (and putting
that behind a reverse proxy, if needed). This uses `Gunicorn`_, which is pretty
flexible and can be configured for pretty much any setup.

.. _`Gunicorn`: http://gunicorn.org/

Note that your Redis instance has to have a version greater than v2.8.0
for the live updates to work.

Also look at the configuration in ``saltobserver/config.py``.
