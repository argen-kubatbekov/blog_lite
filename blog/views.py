from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response

from .models import Post, SubPost, PostLike
from .serializers import PostSerializer, SubPostSerializer, PostCreateItemSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author").prefetch_related("subposts", "liked_by")
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create" and isinstance(self.request.data, list):
            return PostCreateItemSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        if isinstance(request.data, list):
            serializer = self.get_serializer(data=request.data, many=True, context={"request": request})
            serializer.is_valid(raise_exception=True)
            posts = serializer.save()
            return Response(PostSerializer(posts, many=True, context={"request": request}).data,
                            status=status.HTTP_201_CREATED)
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        post = self.get_object()
        like, created = PostLike.objects.get_or_create(post=post, user=request.user)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        return Response({"liked": liked, "likes_count": post.liked_by.count()})

    @action(detail=True, methods=["get"])
    def view(self, request, pk=None):
        Post.objects.filter(pk=pk).update(views_count=F("views_count") + 1)
        post = self.get_object()
        return Response({"id": post.id, "views_count": post.views_count})


class SubPostViewSet(viewsets.ModelViewSet):
    queryset = SubPost.objects.select_related("post")
    serializer_class = SubPostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
