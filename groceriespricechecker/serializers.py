from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Grocery, Message, EmailList, Shop

# Serializer for the Grocery model
class GrocerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Grocery
        fields = '__all__'

# Serializer for user signup
class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    # Validate the username to ensure it is alphanumeric and unique
    def validate_username(self, value):
        if not value.isalnum():
            raise serializers.ValidationError("Username can only contain alphanumeric characters.")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists.")
        return value

    # Validate the email to ensure it is unique
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists.")
        return value

    # Validate the password to ensure it meets complexity requirements
    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        return value

    # Create a new user and send a confirmation email
    def create(self, validated_data):
        try:
            with transaction.atomic():  # Ensure atomicity for user creation and email sending
                user = User.objects.create_user(
                    username=validated_data['username'],
                    email=validated_data.get('email', ''),
                    password=validated_data['password'],
                    first_name=validated_data['first_name'],
                    last_name=validated_data['last_name'],
                )
                user.is_active = False  # Deactivate the user until email confirmation
                user.save()

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                activation_link = f"{settings.FRONTEND_URL}/confirm-email/?uid={uid}&token={token}"

                subject = "Confirm Your Email for Grocery Price Checker"
                context = {
                    'first_name': user.first_name,
                    'activation_link': activation_link
                }
                html_message = render_to_string('emails/confirm_email.html', context)
                plain_message = render_to_string('emails/confirm_email.txt', context)

                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email]
                )
                email_message.attach_alternative(html_message, "text/html")
                email_message.send(fail_silently=False)

                return user
        except Exception as e:
            raise serializers.ValidationError(
                f"An error occurred during signup. Please try again later. ({str(e)})"
            )

# Custom serializer for obtaining JWT tokens
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get("username")
        if identifier and "@" in identifier:  # Check if the identifier is an email
            try:
                user = User.objects.get(email__iexact=identifier)
                attrs["username"] = user.username  # Replace with the actual username
            except User.DoesNotExist:
                pass  # Let authentication fail if no matching user is found

        data = super().validate(attrs)
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

class EmailListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailList
        fields = ['name', 'email', 'origin']

class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = [
            'id',
            'owner',
            'name',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
            'phone_number',
            'email',
            'website',
            'description',
            'latitude',
            'longitude',
            'opening_hours',
            'image_url',
            'created_at',
            'updated_at',
            'active',
            'deleted'
        ]
