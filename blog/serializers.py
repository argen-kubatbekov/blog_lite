from django.db import transaction
from rest_framework import serializers
from .models import Post, SubPost

class SubPostSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = SubPost
        fields = ["id", "title", "body", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class PostSerializer(serializers.ModelSerializer):
    author = serializers.PrimaryKeyRelatedField(read_only=True)
    subposts = SubPostSerializer(many=True, required=False)
    likes_count = serializers.IntegerField(source="liked_by.count", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id", "title", "body", "author",
            "views_count", "likes_count",
            "created_at", "updated_at",
            "subposts",
        ]
        read_only_fields = ["views_count", "likes_count", "created_at", "updated_at"]

    def create(self, validated_data):
        subposts_data = validated_data.pop("subposts", [])
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["author"] = request.user

        with transaction.atomic():
            post = Post.objects.create(**validated_data)
            for sp in subposts_data:
                SubPost.objects.create(post=post, **sp)
        return post

    def update(self, instance, validated_data):
        subposts_data = validated_data.pop("subposts", None)

        with transaction.atomic():
            for attr, val in validated_data.items():
                setattr(instance, attr, val)
            instance.save()

            if subposts_data is not None:
                keep_ids = []
                for sp in subposts_data:
                    sp_id = sp.get("id")
                    if sp_id:
                        obj = SubPost.objects.get(id=sp_id, post=instance)
                        obj.title = sp.get("title", obj.title)
                        obj.body = sp.get("body", obj.body)
                        obj.save()
                        keep_ids.append(obj.id)
                    else:
                        obj = SubPost.objects.create(post=instance, **sp)
                        keep_ids.append(obj.id)
                SubPost.objects.filter(post=instance).exclude(id__in=keep_ids).delete()

        return instance


class PostBulkCreateSerializer(serializers.ListSerializer):
    def create(self, validated_data):
        request = self.context.get("request")
        author = request.user if request and request.user.is_authenticated else None
        objs = [Post(author=author, **item) for item in validated_data]
        return Post.objects.bulk_create(objs)


class PostCreateItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "body"]
    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs["child"] = cls()
        return PostBulkCreateSerializer(*args, **kwargs)
