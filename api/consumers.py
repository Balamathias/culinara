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


# class PostConsumer(ListModelMixin, GenericAsyncAPIConsumer):

#     queryset = Post.objects.all()
#     serializer_class = PostSerializer
#     permissions = (permissions.AllowAny,)

#     async def connect(self, **kwargs):
#         await self.model_change.subscribe()
#         await super().connect()

#     @model_observer(Post)
#     async def model_change(self, message, observer=None, **kwargs):
#         await self.send_json(message)

#     @model_change.serializer
#     def model_serialize(self, instance, action, **kwargs):
#         return dict(
#             data=PostSerializer(instance=instance).data, 
#             action=action.value
#           )


# class UserConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
#     queryset = get_user_model().objects.all()
#     serializer_class = UserSerializer
#     permission_classes = (permissions.AllowAny,)
