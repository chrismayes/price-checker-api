from django.conf import settings
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

class BaseModel(models.Model):
    """Common fields for all models."""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

class Shop(BaseModel):
    # Relationship: one auth_user to many shops
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shops')

    name = models.CharField(max_length=255)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    opening_hours = models.TextField()

    def __str__(self):
        return self.name

class ShoppingList(BaseModel):
    # Relationship: many shopping_list to one auth_user
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shopping_lists')

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class UserGrocery(BaseModel):
    # Relationships:
    # - Many user_grocery to one shopping_list
    # - Many user_grocery to one auth_user
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name='user_groceries')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_groceries')

    def __str__(self):
        return f"UserGrocery {self.id}"

class GroceryItem(BaseModel):
    # Relationship: many grocery_item to one user_grocery
    user_grocery = models.ForeignKey(UserGrocery, on_delete=models.CASCADE, related_name='grocery_items')

    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=50, blank=True, null=True)
    unit = models.CharField(max_length=50, blank=True, null=True)
    packaging_size = models.CharField(max_length=100, blank=True, null=True)
    image = models.URLField(blank=True, null=True)  # Or use ImageField if you configure media storage

    def __str__(self):
        return self.name

class Price(BaseModel):
    # Relationships:
    # - Many price to one user_grocery
    # - One price to many price_shop (see PriceShop model)
    user_grocery = models.ForeignKey(UserGrocery, on_delete=models.CASCADE, related_name='prices')

    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_discounted = models.BooleanField(default=False)
    price_before_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"{self.price} (Discounted: {self.is_discounted})"

class PriceShop(BaseModel):
    # Relationships:
    # - Many price_shop to one price
    # - Many price_shop to one shop
    price = models.ForeignKey(Price, on_delete=models.CASCADE, related_name='price_shops')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='price_shops')

    def __str__(self):
        return f"PriceShop for Price ID {self.price.id} at Shop {self.shop.name}"
