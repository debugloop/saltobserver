gunicorn --log-file=saltobserver_gunicorn.log -k flask_sockets.worker saltobserver:app
