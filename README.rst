=============
Salt Observer
=============

This is a simple webapp for presenting data as offered by `Salt's Redis
Returner`_. It supports searching for functions, history of minions regarding a
certain function and for job IDs.

The function and history views are updated in realtime using socket.io. It also
makes a decent example for using Flask_ with `gevent-socketio`_.

.. _`Salt's Redis Returner`: https://github.com/saltstack/salt/blob/develop/salt/returners/redis_return.py
.. _Flask: http://flask.pocoo.org/
.. _`gevent-socketio`: https://github.com/abourget/gevent-socketio

Running it:
~~~~~~~~~~~
If your minions return their data to some Redis instance, it is as simple as
running ``python saltobserver.py`` (and putting that behind a reverse proxy,
if needed).

Note that your Redis instance has to be fairly recent, as the live updating
part requires `Redis Keyspace Notifications`_, which are available since Redis
v2.8.0, which you have to compile manually in every major distribution but Arch
(as of 03/2014). Maybe `this Salt state`_ I wrote is useful to you.

.. _`Redis Keyspace Notifications`: http://redis.io/topics/notifications
.. _`this Salt state`: https://github.com/danieljn/salt-states/tree/master/salt/redis

Any static dependencies are included in the ``dependencies`` folder, which also
serves as Flask's static file folder. They all use a MIT license.
