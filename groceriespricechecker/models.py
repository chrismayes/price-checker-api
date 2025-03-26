from django.db import models

class Grocery(models.Model):
    barcode_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    brand = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    store_name = models.CharField(max_length=100, blank=True, null=True)
    store_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    store_price_last_updated = models.DateTimeField(blank=True, null=True)

    # Extra fields for control logic
    manually_entered = models.BooleanField(default=False)
    barcode_api_last_checked = models.DateTimeField(blank=True, null=True)
    barcode_lookup_failed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
