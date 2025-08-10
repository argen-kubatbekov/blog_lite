from django.contrib import admin
from .models import Post, SubPost, PostLike

admin.site.register(Post)
admin.site.register(SubPost)
admin.site.register(PostLike)

