from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class CarbonClientConfig(models.Model):
    name = models.CharField(max_length=255)
    server_ip = models.CharField(max_length=15)
    pickle_port = models.IntegerField(default=2004, validators=[MinValueValidator(1), MaxValueValidator(65535)])

    def __str__(self):
        return f"{self.server_ip}:{self.pickle_port}"


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
    namespace_root = models.CharField(max_length=255)
    delay = models.IntegerField(default=300, validators=[MinValueValidator(0), MaxValueValidator(86400)])
    count = models.IntegerField(default=-1, validators=[MinValueValidator(-1), MaxValueValidator(9999)])

    def __str__(self):
        return f"{self.namespace_root}.{self.application_name}"
