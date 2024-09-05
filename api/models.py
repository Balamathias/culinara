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
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, AbstractUser
from django.contrib.auth.models import PermissionsMixin

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

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
    metadata = models.JSONField(default=dict, null=True, blank=True)
    joined = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['username']

    def get_full_name(self):
        return self.username
    

class Tag(models.Model):
    title = models.CharField(max_length=100, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title
    

class Post(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=1000, null=True)
    short_description = models.TextField(null=True, blank=True)
    content = models.TextField()
    thumbnail = models.TextField(null=True, blank=True)
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
