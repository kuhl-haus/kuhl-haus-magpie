import os


# Background Tasks
THREAD_POOL_SIZE: int = int(os.environ.get("THREAD_POOL_SIZE", 20))


# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
APP_LOGS_PATH = os.environ.get("APP_LOGS_PATH")

# Graphite Settings
# Set CARBON_SERVER_IP environment variable to enable sending metrics to Graphite
CARBON_CONFIG = {
    "server_ip": os.environ.get("CARBON_SERVER_IP", None),
    "pickle_port": os.environ.get("CARBON_PICKLE_PORT", 2004),
}
NAMESPACE_ROOT = os.environ.get("NAMESPACE_ROOT", "default")
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "dev")

# Optional pod name for Kubernetes containers
POD_NAME = os.environ.get("POD_NAME")
