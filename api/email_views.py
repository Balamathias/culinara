
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator as token_generator
from django.utils.encoding import force_str
from django.utils.encoding import force_bytes

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

from .serializers import RegisterSerializer

from .models import User


class RegisterView(CreateAPIView):
    """A view that subclasses the `CreateAPIView` to perform User registration functionalities"""

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

            # Generate email verification token
            self.send_verification_email(user, request)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = dict(
                message="Registration Successful. Please verify your email.",
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
        
    def perform_create(self, serializer):
        user = serializer.save()
        return user

    def send_verification_email(self, user, request):
        current_site = get_current_site(request)
        mail_subject = 'Activate your account.'
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        verification_link = reverse('email-verify', kwargs={'uidb64': uid, 'token': token})
        activation_url = f"http://{current_site.domain}{verification_link}"

        # Sending Email
        message = render_to_string('account/activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'activation_url': activation_url,
        })

        send_mail(
            mail_subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )


class EmailVerify(APIView):
    """Verify your Email here:::
    A function that exposes the view for verifying an Email.
    """
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            
            if user and token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({'message': 'Email verified successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
        