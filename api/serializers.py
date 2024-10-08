from typing import Dict
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as DefaultTokenObtainPairSerializer
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
    id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'password', 'avatar', 'metadata', 'username',)

    def validate(self, attrs):
        self.validate_username(attrs.get('username'))
        return attrs
    
    def get_id(self, obj):
        return obj.id
    
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
        
        # if not username.isalnum():
        #     raise serializers.ValidationError("Username should contain only alphanumeric characters")
        return username

    def create(self, validated_data):
        user: User = User.objects.create(
            **validated_data,
        )
        
        user.set_password(validated_data['password'])
        user.save()

        return user


class UserSerializer(serializers.ModelSerializer):

    followers = serializers.SerializerMethodField()
    following = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone', 'avatar', 'metadata', 'followers', 'following']

    def create(self, validated_data):
        user: User = User.objects.create_user(**validated_data)
        return user

    def get_followers(self, obj):
        return obj.followers.values_list('id', flat=True)

    def get_following(self, obj):
        return obj.following.values_list('id', flat=True)


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class PostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    tags = serializers.ListField(child=serializers.CharField(), write_only=True)

    class Meta:
        model = Post
        fields = '__all__'

    def get_likes(self, obj):
        return [user.id for user in obj.likes.all()]

    def get_likes_count(self, obj):
        return obj.likes.count()

    def to_representation(self, instance):
        """Customize output to include tags."""
        representation = super().to_representation(instance)
        representation['tags'] = [tag.name for tag in instance.tags.all()]
        return representation

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        post = Post.objects.create(**validated_data)
        
        tag_objects = []
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tag_objects.append(tag)

        post.tags.set(tag_objects)
        post.save()

        return post

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', [])
        post = super().update(instance, validated_data)

        tag_objects = []
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            tag_objects.append(tag)

        post.tags.set(tag_objects)
        post.save()

        return post
