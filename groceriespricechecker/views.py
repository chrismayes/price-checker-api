import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import EmailMessage, send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Grocery
from .serializers import GrocerySerializer, UserSignupSerializer, CustomTokenObtainPairSerializer, MessageSerializer
from .throttles import FixedIntervalForgotPasswordThrottle

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

        # Build email details for the admin
        subject = f"New Contact Us Message: {request.data.get('subject', 'No Subject')}"
        name = request.data.get('name', 'Anonymous')
        email_sender = request.data.get('email', 'No Email Provided')
        message_text = request.data.get('message', '')
        message_body = (
            f"Message from {name} <{email_sender}>:\n\n"
            f"{message_text}"
        )

        # Send email to the admin
        send_mail(
            subject,
            message_body,
            settings.DEFAULT_FROM_EMAIL,  # Ensure this is set (or use 'admin@groceryPriceChecker.com' directly)
            ['admin@groceryPriceChecker.com'],
            fail_silently=False,
        )

        return Response({'message': 'Your message has been received. Thank you!'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [FixedIntervalForgotPasswordThrottle]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Generic response to prevent email enumeration
            return Response({
                "message": "If an account exists with that email, password reset instructions have been sent."
            })

        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = f"{settings.FRONTEND_URL}/reset-password/?uid={uidb64}&token={token}"

        subject = "Password Reset for Grocery Price Checker"
        context = {
            'first_name': user.first_name,
            'reset_link': reset_link
        }

        # Render the HTML version of the email
        html_message = render_to_string('emails/password_reset.html', context)
        plain_message = render_to_string('emails/password_reset.txt', context)

        # Send both HTML and plain text versions
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email_message.attach_alternative(html_message, "text/html")
        email_message.send(fail_silently=False)

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

@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_email(request):
    uidb64 = request.data.get('uid')
    token = request.data.get('token')

    if not uidb64 or not token:
        return Response({"error": "Missing uid or token."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (DjangoUnicodeDecodeError, User.DoesNotExist):
        return Response({"error": "Invalid uid."}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

    # Activate the user account
    user.is_active = True
    user.save(update_fields=['is_active'])

    return Response({"message": "Email confirmed successfully. You can now log in."}, status=status.HTTP_200_OK)
