from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from kuhl_haus.magpie.endpoints.models import DnsResolver, DnsResolverList, EndpointModel


@pytest.fixture
def dns_resolver_data():
    return {
        'name': 'Google DNS',
        'ip_address': '8.8.8.8'
    }


@pytest.fixture
def dns_resolver_list_data():
    return {
        'name': 'Public DNS Servers'
    }


@pytest.fixture
def endpoint_model_data():
    return {
        'mnemonic': 'test-api',
        'hostname': 'api.example.com',
        'scheme': 'https',
        'port': 443,
        'path': '/api/v1',
        'query': 'format=json',
        'fragment': 'section1',
        'healthy_status_code': 200,
        'json_response': True,
        'status_key': 'status',
        'healthy_status': 'OK',
        'version_key': 'version',
        'connect_timeout': 5.0,
        'read_timeout': 10.0,
        'ignore': False
    }


def test_dns_resolver_str_representation():
    """Test DnsResolver string representation."""
    # Arrange
    name = 'Google DNS'
    ip_address = '8.8.8.8'
    sut = DnsResolver(name=name, ip_address=ip_address)

    # Act
    result = str(sut)

    # Assert
    assert result == f"{name} ({ip_address})"


def test_endpoint_model_str_representation():
    """Test EndpointModel string representation."""
    # Arrange
    mnemonic = 'test-api'
    hostname = 'api.example.com'
    sut = EndpointModel(mnemonic=mnemonic, hostname=hostname)

    # Act
    result = str(sut)

    # Assert
    assert result == f"{mnemonic} - {hostname}"


def test_endpoint_model_default_values():
    """Test EndpointModel default values without DB access."""
    # Arrange
    # Act
    sut = EndpointModel(mnemonic='test', hostname='example.com')

    # Assert
    assert sut.scheme == 'https'
    assert sut.port == 443
    assert sut.path == '/'
    assert sut.healthy_status_code == 200
    assert sut.json_response is True
    assert sut.status_key == 'status'
    assert sut.healthy_status == 'OK'
    assert sut.version_key == 'version'
    assert sut.connect_timeout == 7.0
    assert sut.read_timeout == 7.0
    assert sut.ignore is False


def test_endpoint_model_validators():
    """Test that EndpointModel has proper validators."""
    # Arrange
    # This test verifies that the validators are set up correctly
    # without actually running them
    sut = EndpointModel(mnemonic='test', hostname='example.com')

    # Act
    port_field = sut._meta.get_field('port')
    port_field.validate(443, sut)
    validators = port_field.validators

    # Assert
    # Simply check that validators exist
    assert len(validators) > 0


@patch('django.db.models.fields.CharField')
def test_endpoint_model_scheme_choices(mock_char_field):
    """Test EndpointModel scheme field choices structure."""
    # Arrange
    expected_choices = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
    ]

    # Act
    actual_choices = EndpointModel.SCHEME_CHOICES

    # Assert
    assert actual_choices == expected_choices


def test_dns_resolver_fields():
    """Test DnsResolver model fields."""
    # Arrange
    # Act
    name_field = DnsResolver._meta.get_field('name')
    ip_field = DnsResolver._meta.get_field('ip_address')

    # Assert
    assert name_field.max_length == 255
    assert ip_field.max_length == 255
    assert not name_field.null
    assert not ip_field.null


def test_dns_resolver_list_fields():
    """Test DnsResolverList model fields."""
    # Arrange
    # Act
    name_field = DnsResolverList._meta.get_field('name')
    resolvers_field = DnsResolverList._meta.get_field('resolvers')

    # Assert
    assert name_field.max_length == 255
    assert not name_field.null
    assert resolvers_field.related_model == DnsResolver
    assert resolvers_field.remote_field.related_name == 'resolver_lists'


def test_endpoint_model_fields():
    """Test EndpointModel fields."""
    # Arrange
    # Act
    mnemonic_field = EndpointModel._meta.get_field('mnemonic')
    hostname_field = EndpointModel._meta.get_field('hostname')
    scheme_field = EndpointModel._meta.get_field('scheme')
    dns_resolver_list_field = EndpointModel._meta.get_field('dns_resolver_list')

    # Assert
    assert mnemonic_field.max_length == 255
    assert hostname_field.max_length == 255
    assert scheme_field.max_length == 10
    assert scheme_field.choices == EndpointModel.SCHEME_CHOICES
    assert scheme_field.default == 'https'
    assert dns_resolver_list_field.null
    assert dns_resolver_list_field.remote_field.on_delete.__name__ == 'SET_NULL'
    assert dns_resolver_list_field.related_model == DnsResolverList


def test_dns_resolver_empty_fields():
    """Test creating a DnsResolver with empty required fields raises validation error."""
    # Arrange
    # Act & Assert
    with pytest.raises(ValidationError):
        sut = DnsResolver(name='', ip_address='')
        sut.full_clean()


def test_endpoint_model_invalid_port():
    """Test EndpointModel with invalid port values."""
    # Arrange
    # Act & Assert
    with pytest.raises(ValidationError):
        sut = EndpointModel(
            mnemonic='test',
            hostname='example.com',
            port=0  # Invalid: below minimum value
        )
        sut.full_clean()

    with pytest.raises(ValidationError):
        sut = EndpointModel(
            mnemonic='test',
            hostname='example.com',
            port=65536  # Invalid: above maximum value
        )
        sut.full_clean()


def test_endpoint_model_required_fields():
    """Test EndpointModel required fields."""
    # Arrange
    # Act & Assert
    with pytest.raises(ValidationError):
        sut = EndpointModel(hostname='example.com')  # Missing mnemonic
        sut.full_clean()

    with pytest.raises(ValidationError):
        sut = EndpointModel(mnemonic='test')  # Missing hostname
        sut.full_clean()
