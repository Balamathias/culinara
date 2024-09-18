from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError

from api.models import User
from api.serializers import RegisterSerializer, UserSerializer

class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            # Generate and send OTP
            user.generate_otp()
            self.send_otp_email(user)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = dict(
                message="Registration successful. Please check your email for the OTP.",
                status="success",
                code=status.HTTP_201_CREATED,
                data=dict(
                    user=serializer.data,
                    access_token=access_token,
                    refresh_token=refresh_token,
                )
            )
            return Response(response, status=status.HTTP_201_CREATED, headers=headers)

        except ValidationError as e:
            response = dict(
                status="Bad request",
                message='Registration failed',
                code=status.HTTP_400_BAD_REQUEST,
                errors=e.detail,
                data=None
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
        except:
            user = User.objects.filter(email=request.data.get('email')).first()
            if user:
                user.delete()
            response = dict(
                status="Bad request",
                message='Registration failed',
                code=status.HTTP_400_BAD_REQUEST,
                errors=[{}],
                data=None
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
    def perform_create(self, serializer):
        user = serializer.save()
        return user

    def send_otp_email(self, user):
        mail_subject = 'Culinara - Your OTP for account verification'
        message = f"Hello {user.username},\n\nYour OTP for account verification is: {user.otp}\n\nThis OTP is valid for 15 minutes.\n\nThanks for choosing Culinara."
        send_mail(
            mail_subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )


class VerifyOTPView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        otp_input = request.data.get('otp')
        email = request.data.get('email')

        if not otp_input or not email:
            return Response({'error': 'OTP and email are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            if user.is_otp_valid(otp_input):
                user.is_active = True  # Activate the user
                user.otp = None  # Clear the OTP
                user.otp_created_at = None  # Clear OTP timestamp
                user.save()

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                return Response({
                    'message': 'OTP verified successfully. Account is now active.',
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }, status=status.HTTP_200_OK)

            else:
                return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class ResendOTPView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            if user.is_active:
                return Response({'error': 'User is already active.'}, status=status.HTTP_400_BAD_REQUEST)

            # Generate and send new OTP
            user.generate_otp()
            self.send_otp_email(user)

            return Response({'message': 'OTP has been resent.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as e:
            response = dict(
                status="Bad request",
                message='Wait for at least two minutes before requesting for a new code.',
                code=status.HTTP_400_BAD_REQUEST,
                errors=[{}],
                data=None
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

    def send_otp_email(self, user):
        mail_subject = 'Your OTP for account verification for Culinara'
        message = f"Hello {user.username},\n\nYour new OTP for account verification is: {user.otp}\n\nThis OTP is valid for 15 minutes.\n\nThanks for choosing Culinara."
        send_mail(
            mail_subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
