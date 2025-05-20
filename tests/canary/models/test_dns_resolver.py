import json

from kuhl_haus.magpie.canary.models.dns_resolver import DnsResolver, DnsResolverList


# Using IP addresses from the 192.0.2.0/24 range (TEST-NET-1) which is reserved for
# documentation and examples as per RFC 5737. These addresses are guaranteed to not be
# routable on the public internet, making them ideal for unit testing.


def test_dns_resolver_creation():
    """Test that a DnsResolver object can be created with the expected attributes."""
    # Arrange
    name = "Test DNS"
    ip_address = "192.0.2.1"

    # Act
    sut = DnsResolver(name=name, ip_address=ip_address)

    # Assert
    assert sut.name == name
    assert sut.ip_address == ip_address


def test_dns_resolver_to_json():
    """Test that a DnsResolver can be serialized to JSON."""
    # Arrange
    sut = DnsResolver(name="Alpha DNS", ip_address="192.0.2.2")

    # Act
    result = sut.to_json()

    # Assert
    assert json.loads(result) == {"name": "Alpha DNS", "ip_address": "192.0.2.2"}


def test_dns_resolver_from_dict():
    """Test that a DnsResolver can be created from a dictionary."""
    # Arrange
    data = {"name": "Beta DNS", "ip_address": "192.0.2.3"}

    # Act
    sut = DnsResolver.from_dict(data)

    # Assert
    assert sut.name == "Beta DNS"
    assert sut.ip_address == "192.0.2.3"


def test_dns_resolver_list_creation():
    """Test that a DnsResolverList object can be created with the expected attributes."""
    # Arrange
    resolver1 = DnsResolver(name="Primary DNS", ip_address="192.0.2.4")
    resolver2 = DnsResolver(name="Secondary DNS", ip_address="192.0.2.5")

    # Act
    sut = DnsResolverList(name="default" ,resolvers=[resolver1, resolver2])

    # Assert
    assert len(sut.resolvers) == 2
    assert sut.name == "default"
    assert sut.resolvers[0].name == "Primary DNS"
    assert sut.resolvers[0].ip_address == "192.0.2.4"
    assert sut.resolvers[1].name == "Secondary DNS"
    assert sut.resolvers[1].ip_address == "192.0.2.5"


def test_dns_resolver_list_to_json():
    """Test that a DnsResolverList can be serialized to JSON."""
    # Arrange
    resolver1 = DnsResolver(name="First DNS", ip_address="192.0.2.6")
    resolver2 = DnsResolver(name="Second DNS", ip_address="192.0.2.7")
    sut = DnsResolverList(name="default", resolvers=[resolver1, resolver2])

    # Act
    result = sut.to_json()

    # Assert
    expected = {
        "name": "default",
        "resolvers": [
            {"name": "First DNS", "ip_address": "192.0.2.6"},
            {"name": "Second DNS", "ip_address": "192.0.2.7"}
        ]
    }
    assert json.loads(result) == expected


def test_dns_resolver_list_from_dict():
    """Test that a DnsResolverList can be created from a dictionary."""
    # Arrange
    data = {
        "name": "default",
        "resolvers": [
            {"name": "Main DNS", "ip_address": "192.0.2.8"},
            {"name": "Backup DNS", "ip_address": "192.0.2.9"}
        ]
    }

    # Act
    sut = DnsResolverList.from_dict(data)

    # Assert
    assert len(sut.resolvers) == 2
    assert sut.name == "default"
    assert sut.resolvers[0].name == "Main DNS"
    assert sut.resolvers[0].ip_address == "192.0.2.8"
    assert sut.resolvers[1].name == "Backup DNS"
    assert sut.resolvers[1].ip_address == "192.0.2.9"


def test_dns_resolver_list_empty():
    """Test that a DnsResolverList can be created with an empty list of resolvers."""
    # Arrange & Act
    sut = DnsResolverList(name="default", resolvers=[])

    # Assert
    assert len(sut.resolvers) == 0
    assert sut.resolvers == []


def test_dns_resolver_equality():
    """Test that two DnsResolver objects with the same attributes are equal."""
    # Arrange
    resolver1 = DnsResolver(name="Identical DNS", ip_address="192.0.2.12")
    resolver2 = DnsResolver(name="Identical DNS", ip_address="192.0.2.12")

    # Act & Assert
    assert resolver1 == resolver2


def test_dns_resolver_inequality():
    """Test that two DnsResolver objects with different attributes are not equal."""
    # Arrange
    resolver1 = DnsResolver(name="First DNS", ip_address="192.0.2.13")
    resolver2 = DnsResolver(name="Different DNS", ip_address="192.0.2.14")

    # Act & Assert
    assert resolver1 != resolver2
