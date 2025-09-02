"""
Configuração Gunicorn para AutoU Email Classifier - Produção
"""

import multiprocessing
import os

# Endereço e porta
bind = "0.0.0.0:8000"

# Workers
workers = multiprocessing.cpu_count() * 2 + 1  # Fórmula recomendada
worker_class = "sync"  # ou "gevent" para async
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logs
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Processo
pidfile = "logs/gunicorn.pid"
daemon = False  # False para Docker, True para systemd
user = None  # ou "www-data" em servidores
group = None  # ou "www-data" em servidores

# Segurança
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload
preload_app = True  # Carrega app antes de forkar workers

# Restart
max_requests = 1000  # Restart worker após N requests
max_requests_jitter = 50  # Jitter para evitar restart simultâneo

# SSL (se necessário)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Hooks
def on_starting(server):
    server.log.info("🚀 AutoU Email Classifier iniciando...")

def on_reload(server):
    server.log.info("🔄 Recarregando configuração...")

def worker_int(worker):
    worker.log.info("👷 Worker interrompido")

def pre_fork(server, worker):
    server.log.info(f"👷 Worker {worker.pid} sendo criado")

def post_fork(server, worker):
    server.log.info(f"👷 Worker {worker.pid} criado com sucesso")

def post_worker_init(worker):
    worker.log.info(f"👷 Worker {worker.pid} inicializado")

def worker_abort(worker):
    worker.log.info(f"👷 Worker {worker.pid} abortado")

def pre_exec(server):
    server.log.info("🔄 Preparando para exec")

def when_ready(server):
    server.log.info("✅ Servidor pronto para receber requisições")

def pre_request(worker, req):
    worker.log.debug(f"📥 Processando: {req.uri}")

def post_request(worker, req, environ, resp):
    worker.log.debug(f"📤 Concluído: {req.uri} - {resp.status}")
