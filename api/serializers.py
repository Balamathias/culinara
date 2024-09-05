from typing import Dict
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as DefaultTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView as DefaultTokenObtainPairView
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.permissions import AllowAny

from .models import Post, Tag, User


class TokenObtainPairSerializer(DefaultTokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email

        return token
    

class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
              required=True,
              validators=[UniqueValidator(queryset=User.objects.all())]
            )

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'password', 'avatar', 'metadata', 'username',)

    def validate(self, attrs):
        self.validate_username(attrs.get('username'))
        return attrs
    
    def validate_username(self, username: str) -> str:
        """Validate a User's username
        - Is the name taken?
        - Does it contain the appropriate characters?

        Args:
            username (str): The username to validate

        Raises:
            serializers.ValidationError: Will scream and return a validation error.

        Returns:
            str: an affirmation that all went well
        """
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username is already taken")
        
        if not username.isalnum():
            raise serializers.ValidationError("Username should contain only alphanumeric characters")
        return username

    def create(self, validated_data):
        user: User = User.objects.create(
            **validated_data,
        )
        
        user.set_password(validated_data['password'])
        user.save()

        return user


class UserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'avatar', 'metadata']

    def create(self, validated_data):
        user: User = User.objects.create_user(**validated_data)
        return user


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):

    author = UserSerializer()
    likes = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)

    class Meta:
        model = Post
        fields = '__all__'

    def get_likes(self, obj):
        return [{"id": user.id, "username": user.username} for user in obj.likes.all()]

    def get_likes_count(self, obj):
        return len(obj.likes.all())
    

class TokenObtainPairSerializer(DefaultTokenObtainPairView):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email

        return token
    
    permission_classes = [AllowAny]
