Salt Observer
=============

This is a simple webapp for presenting data as offered by `Salt's Redis
Returner`_ written in `Flask`_. A static demo is available `here`_.

.. _`Salt's Redis Returner`: https://github.com/saltstack/salt/blob/develop/salt/returners/redis_return.py
.. _`Flask`: http://flask.pocoo.org/
.. _`here`: http://analogbyte.github.io/saltobserver/

.. image:: http://files.danieln.de/public/saltobserver.png
   :alt: Screenshot of Saltobserver (17-12-2014)
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
- live updates for the function view using websockets and `Redis' Keyspace
  Notifications`_
- a collapsible representation of raw job data using the awesome `renderjson`_

.. _`Redis Keyspace Notifications`: http://redis.io/topics/notifications
.. _`renderjson`: https://github.com/caldwell/renderjson

Running it
~~~~~~~~~~

If your minions return their data to some Redis instance, it is as
simple as running ``./run.sh`` (and putting that behind a reverse proxy,
if needed). This uses `Gunicorn <http://gunicorn.org/>`__, which is
pretty flexible and can be configured for pretty much any setup.

Note that your Redis instance has to have a version greater than v2.8.0
for the live updates to work.

Also look at the configuration in ``saltobserver/config.py``.
