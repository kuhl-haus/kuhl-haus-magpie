import os

DEFAULT_CANARY_INVOCATION_INTERVAL: int = int(os.environ.get("DEFAULT_CANARY_INVOCATION_INTERVAL", 300))  # Five minutes
DEFAULT_CANARY_INVOCATION_COUNT: int = int(os.environ.get("DEFAULT_CANARY_INVOCATION_COUNT", -1))  # repeats indefinitely
CONFIG_API = os.environ.get('CONFIG_API')
CANARY_CONFIG_FILE_PATH: str = os.environ.get("CANARY_CONFIG_FILE_PATH", "./config/canary.json")
RESOLVERS_CONFIG_FILE_PATH: str = os.environ.get("RESOLVERS_CONFIG_FILE_PATH", "./config/resolvers.json")