# gunicorn.conf.py
bind = "0.0.0.0:10000"
workers = 1
timeout = 240
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 100
preload_app = True
