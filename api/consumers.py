import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from djangochannelsrestframework import permissions
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.mixins import ListModelMixin
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin

from django.contrib.auth import get_user_model

from .models import Post
from .serializers import PostSerializer, UserSerializer


class PostConsumer(ListModelMixin, GenericAsyncAPIConsumer):

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permissions = (permissions.AllowAny,)

    async def connect(self, **kwargs):
        await self.model_change.subscribe()
        await super().connect()

    @model_observer(Post)
    async def model_change(self, message, observer=None, **kwargs):
        await self.send_json(message)

    @model_change.serializer
    def model_serialize(self, instance, action, **kwargs):
        return dict(
            data=PostSerializer(instance=instance).data, 
            action=action.value
          )


class UserConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)


class LikeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'post_{self.post_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json.get('action')

        if action == 'like':
            # Interact with the Post model
            post = await self.get_post(self.post_id)
            if post:
                post.likes.add(self.scope['user'] if self.scope['user'].is_authenticated else 'Anonymous')
                await self.update_likes(post)
                # Send updated like count to the group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'like_update',
                        'like_count': post.likes.count()
                    }
                )

    # Receive message from room group
    async def like_update(self, event):
        like_count = event['like_count']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'like_count': like_count
        }))

    @database_sync_to_async
    def get_post(self, post_id):
        try:
            return Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return None

    @database_sync_to_async
    def update_likes(self, post):
        post.save()
