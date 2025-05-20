import pickle
import socket
import struct
from typing import List


class CarbonPoster:
    server_ip: str
    pickle_port: int

    def __init__(self, server_ip: str, pickle_port: int):
        if not isinstance(server_ip, str):
            raise TypeError("server_ip must be a string")
        if not isinstance(pickle_port, int):
            raise TypeError("pickle_port must be a int")
        if not 1 <= pickle_port <= 65535:
            raise ValueError("pickle_port must be between 1 and 65535")
        self.server_ip = server_ip
        self.pickle_port = pickle_port

    def post_metrics(self, metrics: List[tuple]):
        if not isinstance(metrics, list):
            raise TypeError("metrics must be a list of tuples")

        if metrics and not all(isinstance(item, tuple) for item in metrics):
            raise TypeError("metrics must be a list of tuples")

        payload = pickle.dumps(metrics, protocol=2)
        header = struct.pack("!L", len(payload))
        message = header + payload
        with socket.socket() as sock:
            sock.connect((self.server_ip, self.pickle_port))
            sock.sendall(message)
