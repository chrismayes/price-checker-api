from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Grocery, Message

class GrocerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Grocery
        fields = '__all__'

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def validate_username(self, value):
        # Ensure the username contains only alphanumeric characters.
        if not value.isalnum():
            raise serializers.ValidationError("Username can only contain alphanumeric characters.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    def validate_password(self, value):
        # Password restrictions: at least 8 characters, contains at least one number and one uppercase letter.
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        return value

    def create(self, validated_data):
        # Create user using create_user to hash the password properly.
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        # Optionally mark user as inactive until email confirmation is complete.
        user.is_active = False
        user.save()

        # Generate an email confirmation token and UID.
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        activation_link = f"{settings.FRONTEND_URL}/confirm-email/?uid={uid}&token={token}"
        subject = "Confirm Your Email for Grocery Price Checker"
        message = (
            f"Hi {user.first_name},\n\n"
            "Thank you for signing up for Grocery Price Checker.\n"
            "Please confirm your email address by clicking the link below:\n\n"
            f"{activation_link}\n\n"
            "If you did not sign up for this account, please ignore this email.\n\n"
            "Thanks,\n"
            "The Grocery Price Checker Team"
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,  # e.g. 'admin@grocerypricechecker.com'
            [user.email],
            fail_silently=False,
        )

        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Check if the identifier (sent as "username") contains an "@" symbol.
        identifier = attrs.get("username")
        if identifier and "@" in identifier:
            try:
                user = User.objects.get(email__iexact=identifier)
                attrs["username"] = user.username  # Replace with actual username
            except User.DoesNotExist:
                # Let the authentication process fail if no matching user is found
                pass

        data = super().validate(attrs)
        # Update the user's last_login field
        self.user.last_login = timezone.now()
        self.user.save(update_fields=['last_login'])
        return data

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        return token

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
