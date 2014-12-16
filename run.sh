gunicorn --log-file=- -k flask_sockets.worker saltobserver:app
