from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroceryListCreateAPIView, GroceryRetrieveUpdateDestroyAPIView, ShopViewSet
from .product_views import ProductFromBarcodeAPIView

router = DefaultRouter()
router.register(r'shops', ShopViewSet, basename='shop')

urlpatterns = [
    path('groceries/', GroceryListCreateAPIView.as_view(), name='grocery-list-create'),
    path('groceries/<int:pk>/', GroceryRetrieveUpdateDestroyAPIView.as_view(), name='grocery-detail'),
    path('product-from-barcode/', ProductFromBarcodeAPIView.as_view(), name='product-from-barcode'),
    path('', include(router.urls)),
]

