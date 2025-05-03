from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class DnsResolver(models.Model):
    name = models.CharField(max_length=255)
    ip_address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"


class DnsResolverList(models.Model):
    name = models.CharField(max_length=255)
    resolvers = models.ManyToManyField(DnsResolver, related_name='resolver_lists')

    def __str__(self):
        return f"{self.name} ({self.resolvers.count()})"


class EndpointModel(models.Model):
    SCHEME_CHOICES = [
        ('http', 'HTTP'),
        ('https', 'HTTPS'),
    ]

    mnemonic = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255)
    scheme = models.CharField(max_length=10, choices=SCHEME_CHOICES, default='https')
    port = models.IntegerField(default=443, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    query = models.CharField(max_length=255, null=True, blank=True)
    fragment = models.CharField(max_length=255, null=True, blank=True)
    healthy_status_code = models.IntegerField(default=200)
    json_response = models.BooleanField(default=True)
    status_key = models.CharField(max_length=255, default="status")
    healthy_status = models.CharField(max_length=255, default="OK")
    version_key = models.CharField(max_length=255, default="version")
    connect_timeout = models.FloatField(default=7.0)
    read_timeout = models.FloatField(default=7.0)
    ignore = models.BooleanField(default=False)
    path = models.CharField(max_length=255, default="/")
    dns_resolver_list = models.ForeignKey(
        DnsResolverList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='endpoints'
    )

    def __str__(self):
        return f"{self.mnemonic} - {self.hostname}"
