from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Follow, User
from .pagination import CustomPageNumberPagination
from .serializers import FollowSerializer


class CustomUserViewSet(UserViewSet):
    pagination_class = CustomPageNumberPagination

    @action(detail=True, methods=['post'],
            permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if user == author:
            return Response(
                {'errors': 'Невозможно подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if Follow.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Подписка на данного пользователя уже существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        follow = Follow.objects.create(user=user, author=author)
        serializer = FollowSerializer(
            follow, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def del_subscribe(self, request, id=None):
        author = get_object_or_404(User, pk=id)
        if request.user == author:
            return Response(
                {'errors': 'Отписаться от себя невозможно'},
                status=status.HTTP_400_BAD_REQUEST
            )
        follow = Follow.objects.filter(user=request.user, author=author)
        if not follow.exists():
            return Response(
                {'errors': 'Подписки на пользователя не существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        return self.get_paginated_response(
            FollowSerializer(
                self.paginate_queryset(
                    Follow.objects.filter(user=request.user)
                ),
                many=True,
                context={'request': request}
            ).data
        )
