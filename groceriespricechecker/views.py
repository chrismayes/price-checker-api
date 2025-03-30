import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Grocery
from .serializers import GrocerySerializer, UserSignupSerializer, CustomTokenObtainPairSerializer, MessageSerializer

User = get_user_model()

class GroceryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Grocery.objects.all()
    serializer_class = GrocerySerializer

class GroceryRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Grocery.objects.all()
    serializer_class = GrocerySerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def signup_view(request):
    if not settings.ACCOUNT_CREATION_ENABLED:
        return Response({'detail': 'Account creation is disabled at this time.'},
                        status=status.HTTP_403_FORBIDDEN)

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

class ForgotPasswordView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # To prevent email enumeration, return a generic message even if no user is found
            return Response({
                "message": "If an account exists with that email, password reset instructions have been sent."
            })

        # Generate token and uid
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        reset_link = f"{settings.FRONTEND_URL}/reset-password/?uid={uidb64}&token={token}"

        subject = "Password Reset for Grocery Price Checker"
        message = (
            "Hello,\n\n"
            "We received a request to reset your password for Grocery Price Checker. "
            "Please click the link below to set a new password:\n\n"
            f"{reset_link}\n\n"
            "If you did not request a password reset, please ignore this email.\n\n"
            "Thanks,\n"
            "Grocery Price Checker Team"
        )

        # Send email via SendGrid
        email_message = EmailMessage(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        email_message.send()

        return Response({
            "message": "If an account exists with that email, password reset instructions have been sent."
        })

class ResetPasswordView(APIView):
    def post(self, request):
        uidb64 = request.data.get('uid')
        token = request.data.get('token')
        new_password = request.data.get('new_password')

        if not (uidb64 and token and new_password):
            return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (DjangoUnicodeDecodeError, User.DoesNotExist):
            return Response({"error": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        # Set the new password
        user.set_password(new_password)
        user.save()

        return Response({"message": "Password reset successfully."})
