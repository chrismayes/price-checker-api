from django.urls import path
from .views import GroceryListCreateAPIView, GroceryRetrieveUpdateDestroyAPIView, signup_view
from .product_views import ProductFromBarcodeAPIView  # import the separated view

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('groceries/', GroceryListCreateAPIView.as_view(), name='grocery-list-create'),
    path('groceries/<int:pk>/', GroceryRetrieveUpdateDestroyAPIView.as_view(), name='grocery-detail'),
    path('product-from-barcode/', ProductFromBarcodeAPIView.as_view(), name='product-from-barcode'),
]
