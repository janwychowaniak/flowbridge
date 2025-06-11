import multiprocessing
import yaml
from pathlib import Path

def load_config():
    """Load configuration from config.yaml."""
    config_path = Path("config.yaml")
    if not config_path.exists():
        return {}
    
    with open(config_path) as f:
        return yaml.safe_load(f)

config = load_config()
server_config = config.get('server', {})

# Bind address
bind = f"{server_config.get('host', '0.0.0.0')}:{server_config.get('port', 8000)}"

# Worker configuration
workers = server_config.get('workers', multiprocessing.cpu_count() * 2 + 1)
worker_class = 'sync'
timeout = config.get('general', {}).get('route_timeout', 30)

# Logging
loglevel = server_config.get('log_level', 'info')
accesslog = '-'
errorlog = '-'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
