from urllib import parse

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ScriptConfig(models.Model):
    LOG_LEVEL_CHOICES = [
        ('INFO', 'info'),
        ('DEBUG', 'debug'),
        ('WARNING', 'warning'),
        ('ERROR', 'error'),
    ]

    name = models.CharField(max_length=255)
    application_name = models.CharField(max_length=255)
    log_level = models.CharField(max_length=7, choices=LOG_LEVEL_CHOICES, default='INFO')
    namespace_root = models.CharField(max_length=255, null=True, blank=True)
    metric_namespace = models.CharField(max_length=255, null=True, blank=True)
    carbon_metrics_enabled = models.BooleanField(default=False)
    carbon_server_ip = models.CharField(max_length=15, null=True, blank=True)
    carbon_pickle_port = models.IntegerField(default=2004, validators=[MinValueValidator(1), MaxValueValidator(65535)])

    def __str__(self):
        return f"{self.name}.{self.application_name}"


class DnsResolver(models.Model):
    name = models.CharField(max_length=255)
    ip_address = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

    def to_json(self):
        return {"name": self.name, "ip_address": self.ip_address}


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
    VERB_CHOICES = [
        ('GET', 'GET'),
        ('PATCH', 'PATCH'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    ]
    RESPONSE_FORMAT_CHOICES = [
        ('json', 'json'),
        ('text', 'text'),
    ]
    ENVIRONMENT_CHOICES = [
        ('alpha', 'alpha'),
        ('beta', 'beta'),
        ('gamma', 'gamma'),
        ('dev', 'dev'),
        ('local', 'local'),
        ('one-box', 'one-box'),
        ('ppe', 'ppe'),
        ('prod', 'prod'),
        ('production', 'production'),
        ('qa', 'qa'),
        ('staging', 'staging'),
        ('test', 'test'),
        ('uat', 'uat'),
        ('zeta', 'zeta'),
    ]

    mnemonic = models.CharField(max_length=255)
    hostname = models.CharField(max_length=255)
    environment = models.CharField(max_length=16, choices=ENVIRONMENT_CHOICES, default='prod')
    scheme = models.CharField(max_length=10, choices=SCHEME_CHOICES, default='https')
    port = models.IntegerField(default=443, validators=[MinValueValidator(1), MaxValueValidator(65535)])
    path = models.CharField(max_length=255, default="/")
    query = models.CharField(max_length=255, null=True, blank=True)
    fragment = models.CharField(max_length=255, null=True, blank=True)
    verb = models.CharField(max_length=6, choices=VERB_CHOICES, default="GET")
    body = models.JSONField(null=True, blank=True)
    healthy_status_code = models.IntegerField(default=200)
    response_format = models.CharField(max_length=16, choices=RESPONSE_FORMAT_CHOICES, default="text", null=True, blank=True)
    status_key = models.CharField(max_length=255, null=True, blank=True)
    healthy_status = models.CharField(max_length=255, null=True, blank=True)
    version_key = models.CharField(max_length=255, null=True, blank=True)
    connect_timeout = models.FloatField(default=7.0)
    read_timeout = models.FloatField(default=7.0)
    ignore = models.BooleanField(default=False)
    health_check = models.BooleanField(default=True)
    tls_check = models.BooleanField(default=True)
    dns_check = models.BooleanField(default=True)
    dns_resolver_list = models.ForeignKey(
        DnsResolverList,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='endpoints'
    )

    def __str__(self):
        return f"{self.mnemonic} - {self.hostname}"

    @staticmethod
    def __normalize_path(path: str) -> str:
        if not path:
            path = "/"
        elif not path.startswith("/"):
            path = f"/{path}"
        # Replace multiple slashes with a single slash
        while '//' in path:
            path = path.replace('//', '/')
        return path

    @property
    def url(self) -> str:
        path = self.__normalize_path(self.path)
        if self.query:
            query_string = parse.urlencode(self.query)
            path = parse.urljoin(path, f"?{query_string}")
        if self.fragment:
            path = parse.urljoin(path, f"#{self.fragment}")
        return f"{self.scheme}://{self.hostname}:{self.port}{path}"
