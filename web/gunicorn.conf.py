# gunicorn config
bind = '0.0.0.0:5000'
workers = 2
threads = 4
timeout = 30
loglevel = 'info'
accesslog = '-' # stdout
errorlog = '-'