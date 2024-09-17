from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.password_validation import validate_password

from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.exceptions import ValidationError

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from rest_framework.views import APIView
from api.models import User


class PasswordResetRequestView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

            context = {
                'user': user,
                'reset_url': reset_url
            }
            subject = "Password Reset Request"
            text_content = f"Hello {user.username},\n\nYou requested a password reset. Click the link below to reset your password:\n{reset_url}"
            html_content = render_to_string('password_reset_email.html', context)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            
            email.attach_alternative(html_content, "text/html")
            email.send()

            return Response({'message': 'Password reset email sent.'}, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)


class PasswordResetTokenValidateView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            token_generator = PasswordResetTokenGenerator()
            if token_generator.check_token(user, token):
                return Response({'message': 'Token is valid.'}, status=status.HTTP_200_OK)
            else:
                raise ValidationError('Invalid token or token has expired.')
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, uidb64, token):
        new_password = request.data.get('password')

        if not new_password:
            return Response({'error': 'New password is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)

            token_generator = PasswordResetTokenGenerator()
            if token_generator.check_token(user, token):
                try:
                    validate_password(new_password, user)
                    user.set_password(new_password)
                    user.save()

                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)

                    return Response({'message': 'Password reset successful.', 'access_token': access_token, 'refresh_token': refresh_token}, status=status.HTTP_200_OK)
                except ValidationError as e:
                    return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'error': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)
        

class ResendPasswordResetView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            if user.is_active:
                token_generator = PasswordResetTokenGenerator()
                token = token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

                context = {
                    'user': user,
                    'reset_url': reset_url
                }
                subject = "Password Reset Request (Resend)"
                text_content = f"Hello {user.username},\n\nYou requested a password reset. Click the link below to reset your password:\n{reset_url}"
                html_content = render_to_string('password_reset_email.html', context)

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                )
                
                email.attach_alternative(html_content, "text/html")
                email.send()

                return Response({'message': 'Password reset email has been resent.'}, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
