import requests
from django.conf import settings
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Grocery
from .serializers import GrocerySerializer, UserSignupSerializer, CustomTokenObtainPairSerializer, MessageSerializer

class GroceryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Grocery.objects.all()
    serializer_class = GrocerySerializer

class GroceryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grocery.objects.all()
    serializer_class = GrocerySerializer

@api_view(['POST'])
@permission_classes([AllowAny])  # This allows unauthenticated users to access the signup endpoint
def signup_view(request):
    serializer = UserSignupSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Signup successful'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def contact_us(request):
    recaptcha_token = request.data.get('recaptchaToken')
    if not recaptcha_token:
        return Response({'recaptcha': ['reCAPTCHA validation failed.']}, status=status.HTTP_400_BAD_REQUEST)

    # Verify the token with Google's reCAPTCHA API
    recaptcha_secret = settings.RECAPTCHA_SECRET_KEY
    recaptcha_response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data={"secret": recaptcha_secret, "response": recaptcha_token},
    )
    recaptcha_result = recaptcha_response.json()
    if not recaptcha_result.get("success"):
        return Response({'recaptcha': ['reCAPTCHA verification failed.']}, status=status.HTTP_400_BAD_REQUEST)

    # Proceed with saving the message
    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Your message has been received. Thank you!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)