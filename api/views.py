import json
import time
from rest_framework.generics import CreateAPIView, DestroyAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Count

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Post, Tag, User
from api.paginations import NextPageNumberPagination, StandardResultsSetPagination
from api.serializers import PostSerializer, RegisterSerializer, TokenObtainPairSerializer, UserSerializer

class ObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = TokenObtainPairSerializer


class RefreshTokenView(TokenRefreshView):
    permission_classes = (AllowAny,)


class RegisterView(CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)

            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            response = dict(
                message="Registration Successful",
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
            print(e)
            response = dict(
                status="Bad request",
                message='Registration failed',
                code=status.HTTP_400_BAD_REQUEST,
                errors=e.detail
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        
    def perform_create(self, serializer):
        user = serializer.save()
        return user


class PostViewSet(ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = (AllowAny,)
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        thumbnail_str = data.get('thumbnail')
        if isinstance(thumbnail_str, str):
            try:
                data['thumbnail'] = json.loads(thumbnail_str)
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format for thumbnail"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(author=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='tags')
    def posts_by_tag(self, request):
        tag_name = request.query_params.get('tag', None)
        
        if tag_name is None:
            return Response({"detail": "Tag query parameter is required."}, status=400)
        
        try:
            tag = Tag.objects.get(name=tag_name)
        except Tag.DoesNotExist:
            return Response({"detail": f"Tag '{tag_name}' not found."}, status=404)
        
        queryset = Post.objects.filter(tags=tag) \
            .annotate(like_count=Count('likes')) \
            .order_by('-like_count', '-created_at')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class LikePostView(CreateAPIView, DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'id'

    def create(self, request, *args, **kwargs) -> Response:
        """Like and Unlike a post
        """
        post: Post = self.get_object()
        if request.user in post.likes.all():
            return self.destroy(request, *args, **kwargs)
        post.likes.add(request.user)
        post.save()
        serializer: PostSerializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs) -> Response:
        """Remove like from a post if user has already liked it."""
        post: Post = self.get_object()
        post.likes.remove(request.user)
        post.save()
        serializer: PostSerializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        data = request.data

        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.avatar = data.get("avatar", user.avatar)
        user.save()

        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "id"
    permission_classes = [IsAuthenticated]


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data)
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Logout successful"}, status=205)
        except Exception as e:
            return Response({"message": "Bad request"}, status=400)


class TrendingPostListView(ListAPIView):
    serializer_class = PostSerializer
    queryset = Post.objects.all()

    def get_queryset(self):
        count = self.request.query_params.get('count', 3)

        try:
            count = int(count)
        except ValueError:
            count = 3

        trending_posts = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count')

        most_recent_most_liked = trending_posts.order_by('-like_count', '-created_at')[:count]

        oldest_most_liked = trending_posts.order_by('-like_count', 'created_at')[:count]

        combined_trending = (most_recent_most_liked | oldest_most_liked).distinct()[:count]

        return combined_trending

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(dict(
            message="Trending Posts fetched successfully",
            data=serializer.data,
        ), status=status.HTTP_200_OK)


class LikedPostsViewSet(ReadOnlyModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        return Post.objects.filter(likes=user).order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='favorites')
    def liked_posts(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
