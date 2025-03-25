from rest_framework import generics
from .models import Grocery
from .serializers import GrocerySerializer

class GroceryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Grocery.objects.all().order_by('-created_at')
    serializer_class = GrocerySerializer
    def perform_create(self, serializer):
        # Ensure manually_entered is set to True when coming from this endpoint
        serializer.save(manually_entered=True)

class GroceryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grocery.objects.all()
    serializer_class = GrocerySerializer
