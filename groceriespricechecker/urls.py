from django.urls import path
from .views import GroceryListCreateAPIView, GroceryRetrieveUpdateDestroyAPIView
from .product_views import ProductFromBarcodeAPIView  # import the separated view

urlpatterns = [
    path('groceries/', GroceryListCreateAPIView.as_view(), name='grocery-list-create'),
    path('groceries/<int:pk>/', GroceryRetrieveUpdateDestroyAPIView.as_view(), name='grocery-detail'),
    path('product-from-barcode/', ProductFromBarcodeAPIView.as_view(), name='product-from-barcode'),
]
