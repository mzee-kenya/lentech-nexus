from django.contrib import admin

from .models import Comment, Post, PostLike


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('created_at',)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'has_media', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('body', 'author__username')
    inlines = [CommentInline]

    @admin.display(boolean=True, description='Media')
    def has_media(self, obj):
        return obj.has_media


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('post', 'user', 'created_at')
    search_fields = ('post__id', 'user__username')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'created_at')
    search_fields = ('body', 'author__username', 'post__id')
