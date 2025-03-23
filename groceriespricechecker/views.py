from rest_framework import generics
from .models import Grocery
from .serializers import GrocerySerializer

class GroceryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Grocery.objects.all()
    serializer_class = GrocerySerializer

class GroceryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grocery.objects.all()
    serializer_class = GrocerySerializer
