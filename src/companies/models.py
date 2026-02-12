from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=120)
    cnpj = models.CharField(max_length=14, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"

    def __str__(self) -> str:
        return self.name
