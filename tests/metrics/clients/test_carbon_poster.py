import pickle
import socket
import struct
from unittest.mock import patch, MagicMock

import pytest

from kuhl_haus.magpie.metrics.clients.carbon_poster import CarbonPoster


@pytest.fixture
def valid_server_config():
    return {
        'server_ip': '127.0.0.1',
        'pickle_port': 2004
    }


@pytest.fixture
def valid_metrics():
    return [
        ('server.cpu.usage', (1600000000, 45.2)),
        ('server.memory.usage', (1600000000, 72.1))
    ]


@pytest.fixture
def carbon_poster(valid_server_config):
    return CarbonPoster(
        server_ip=valid_server_config['server_ip'],
        pickle_port=valid_server_config['pickle_port']
    )


class TestCarbonPosterInit:
    def test_initializes_with_valid_parameters(self, valid_server_config):
        # Arrange
        server_ip = valid_server_config['server_ip']
        pickle_port = valid_server_config['pickle_port']

        # Act
        sut = CarbonPoster(server_ip=server_ip, pickle_port=pickle_port)

        # Assert
        assert sut.server_ip == server_ip
        assert sut.pickle_port == pickle_port

    def test_raises_type_error_when_server_ip_not_str(self):
        # Arrange & Act & Assert
        with pytest.raises(TypeError, match="server_ip"):
            CarbonPoster(server_ip=123, pickle_port=2004)

    def test_raises_type_error_when_pickle_port_not_int(self):
        # Arrange & Act & Assert
        with pytest.raises(TypeError, match="pickle_port"):
            CarbonPoster(server_ip='127.0.0.1', pickle_port='2004')

    def test_raises_value_error_when_pickle_port_out_of_range(self):
        # Arrange & Act & Assert
        with pytest.raises(ValueError, match="pickle_port"):
            CarbonPoster(server_ip='127.0.0.1', pickle_port=70000)


class TestPostMetrics:
    @patch('kuhl_haus.magpie.metrics.clients.carbon_poster.socket.socket')
    def test_sends_valid_metrics_correctly(self, mock_socket, carbon_poster, valid_metrics):
        # Arrange
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance

        expected_payload = pickle.dumps(valid_metrics, protocol=2)
        expected_header = struct.pack("!L", len(expected_payload))
        expected_message = expected_header + expected_payload

        # Act
        carbon_poster.post_metrics(valid_metrics)

        # Assert
        mock_sock_instance.connect.assert_called_once_with(
            (carbon_poster.server_ip, carbon_poster.pickle_port)
        )
        mock_sock_instance.sendall.assert_called_once_with(expected_message)

    @patch('kuhl_haus.magpie.metrics.clients.carbon_poster.socket.socket')
    def test_raises_type_error_when_metrics_not_list(self, mock_socket, carbon_poster):
        # Arrange & Act & Assert
        with pytest.raises(TypeError, match="metrics"):
            carbon_poster.post_metrics("not_a_list")

    @patch('kuhl_haus.magpie.metrics.clients.carbon_poster.socket.socket')
    def test_raises_type_error_when_metrics_items_not_tuples(self, mock_socket, carbon_poster):
        # Arrange & Act & Assert
        with pytest.raises(TypeError, match="metrics"):
            carbon_poster.post_metrics([1, 2, 3])

    @patch('kuhl_haus.magpie.metrics.clients.carbon_poster.socket.socket')
    def test_handles_empty_metrics_list(self, mock_socket, carbon_poster):
        # Arrange
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance

        expected_payload = pickle.dumps([], protocol=2)
        expected_header = struct.pack("!L", len(expected_payload))
        expected_message = expected_header + expected_payload

        # Act
        carbon_poster.post_metrics([])

        # Assert
        mock_sock_instance.sendall.assert_called_once_with(expected_message)

    @patch('kuhl_haus.magpie.metrics.clients.carbon_poster.socket.socket')
    def test_handles_connection_error(self, mock_socket, carbon_poster, valid_metrics):
        # Arrange
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.connect.side_effect = socket.error("Connection refused")

        # Act & Assert
        with pytest.raises(socket.error, match="Connection refused"):
            carbon_poster.post_metrics(valid_metrics)

    @patch('kuhl_haus.magpie.metrics.clients.carbon_poster.socket.socket')
    def test_handles_send_error(self, mock_socket, carbon_poster, valid_metrics):
        # Arrange
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance
        mock_sock_instance.sendall.side_effect = socket.error("Send failed")

        # Act & Assert
        with pytest.raises(socket.error, match="Send failed"):
            carbon_poster.post_metrics(valid_metrics)


class TestFunctionalCore:
    @patch('kuhl_haus.magpie.metrics.clients.carbon_poster.socket.socket')
    def test_functional_approach_with_dependency_injection(self, mock_socket):
        # Arrange
        mock_sock_instance = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock_instance

        # Redefine CarbonPoster as a function with dependency injection
        def create_metric_sender(socket_factory):
            def send_metrics(server_ip, pickle_port, metrics):
                payload = pickle.dumps(metrics, protocol=2)
                header = struct.pack("!L", len(payload))
                message = header + payload

                with socket_factory() as sock:
                    sock.connect((server_ip, pickle_port))
                    sock.sendall(message)

            return send_metrics

        # Create our test function with the mock socket injected
        send_metrics = create_metric_sender(mock_socket)
        server_ip = '127.0.0.1'
        pickle_port = 2004
        metrics = [('test.metric', (1600000000, 99.9))]

        # Act
        send_metrics(server_ip, pickle_port, metrics)

        # Assert
        mock_sock_instance.connect.assert_called_once_with((server_ip, pickle_port))
        expected_payload = pickle.dumps(metrics, protocol=2)
        expected_header = struct.pack("!L", len(expected_payload))
        expected_message = expected_header + expected_payload
        mock_sock_instance.sendall.assert_called_once_with(expected_message)
