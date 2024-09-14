"""
API MODELS
`User`
`Tag`
`Post`

```py AbstractBaseUser
class User(AbstractUser):
    '''This was only necessary for project initialization.'''
    pass
```
"""

from abc import abstractmethod
import datetime
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, AbstractUser
from django.contrib.auth.models import PermissionsMixin

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from django.utils import timezone

from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    @abstractmethod
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
            **extra_fields
        )

        user.set_password(password)

        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **kwargs):
        return self.create_user(email, password, is_superuser=True, is_staff=True, **kwargs)


class User(AbstractBaseUser, PermissionsMixin):

    objects = UserManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    username = models.CharField(max_length=40, blank=True, null=True, unique=True)
    avatar = models.CharField(null=True, blank=True, max_length=2000)
    followers = models.ManyToManyField(
        'self', related_name='following', symmetrical=False, blank=True
    )
    followed_tags = models.ManyToManyField('Tag', related_name='followed_by', blank=True)
    metadata = models.JSONField(default=dict, null=True, blank=True)
    joined = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    def generate_otp(self):
        """Generate a random 6-digit OTP if it doesn't exist or the cooldown period is over."""
        now = timezone.now()
        if not self.otp or (self.otp_created_at and now - self.otp_created_at >= datetime.timedelta(minutes=2)):
            self.otp = str(uuid.uuid4().int)[:6]
            self.otp_created_at = now
            self.save()
        else:
            raise ValueError("OTP was recently sent. Please wait a few minutes.")

    def is_otp_valid(self, otp_input):
        """Check if the provided OTP is valid and not expired."""
        if self.otp == otp_input and self.otp_created_at:
            now = timezone.now()
            expiry_time = self.otp_created_at + datetime.timedelta(minutes=15)
            if now <= expiry_time:
                return True
        return False

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    def get_full_name(self):
        return self.username
    

class Tag(models.Model):
    name = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name
    

class Post(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=1000, null=True)
    short_description = models.TextField(null=True, blank=True)
    content = models.TextField()
    thumbnail = models.JSONField(default=dict, null=True, blank=True)
    video = models.CharField(max_length=2000, null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="posts")
    likes = models.ManyToManyField(User, blank=True, related_name="likes")
    tags = models.ManyToManyField(Tag, related_name="tags", blank=True)

    def __str__(self):
        return self.title if self.title else self.short_description if self.short_description else self.content[:100]


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
