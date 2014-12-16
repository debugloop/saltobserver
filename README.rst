=============
Salt Observer
=============

This is a simple webapp for presenting data as offered by `Salt's Redis
Returner`_ written in `Flask`_. It features:

- a simple and clean interface
- three views:

  * a function view showing all minions that ran a particular function
  * a history view for looking at a minion's history with a specific function
  * a job view listing all minions which ran a specific job

- a customizable navbar, which links to function views
- searchpages for everything
- live updates for the function view using websockets and `Redis Keyspace Notifications`_

.. _`Salt's Redis Returner`: https://github.com/saltstack/salt/blob/develop/salt/returners/redis_return.py
.. _Flask: http://flask.pocoo.org/
.. _`Redis Keyspace Notifications`: http://redis.io/topics/notifications


Running it:
~~~~~~~~~~~
If your minions return their data to some Redis instance, it is as simple as
running ``./run.sh`` (and putting that behind a reverse proxy, if needed).
This uses `Gunicorn`_, which is pretty flexible and can be configured for pretty
much any setup.

.. _`Gunicorn`: http://gunicorn.org/

Note that your Redis instance has to have a version greater than v2.8.0 for the
live updates to work.

Also look at the configuration in ``saltobserver/config.py``.
