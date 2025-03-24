import multiprocessing

# ワーカーの設定
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000

# タイムアウトの設定
timeout = 300  # 5分
keepalive = 24

# バッファの設定
limit_request_line = 0
limit_request_fields = 32768
limit_request_field_size = 0