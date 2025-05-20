import json
from dataclasses import dataclass


@dataclass()
class CarbonConfig:
    server_ip: str
    pickle_port: int

    @staticmethod
    def from_file(file_path):
        with open(file_path) as file:
            file_contents = json.load(file)
        return CarbonConfig(**file_contents)
