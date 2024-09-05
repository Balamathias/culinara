from rest_framework.permissions import AllowAny
from rest_framework.generics import CreateAPIView, DestroyAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import Post, User
from api.serializers import PostSerializer, RegisterSerializer, TokenObtainPairSerializer

class ObtainTokenPairView(TokenObtainPairView):
    permission_classes = (AllowAny,)
    serializer_class = TokenObtainPairSerializer


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
            response = dict(
                status="Bad request",
                message='Registration failed',
                code=status.HTTP_400_BAD_REQUEST,
                errors=e.detail
            )
            return Response(response, status=status.HTTP_400_BAD_REQUEST)


class PostViewSet(ModelViewSet):

    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = (AllowAny,)


class LikePostView(CreateAPIView, DestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (AllowAny,)
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
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs) -> Response:
        """Remove like from a post if user has already liked it."""
        post: Post = self.get_object()
        post.likes.remove(request.user)
        post.save()
        serializer: PostSerializer = self.get_serializer(post)
        return Response(serializer.data)
    