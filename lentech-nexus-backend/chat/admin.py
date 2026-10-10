from django.contrib import admin

from .models import Conversation, ConversationMember, Message


class ConversationMemberInline(admin.TabularInline):
    model = ConversationMember
    extra = 0
    readonly_fields = ('joined_at',)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'title', 'created_by', 'updated_at')
    list_filter = ('kind',)
    search_fields = ('title', 'members__user__username')
    inlines = [ConversationMemberInline]


@admin.register(ConversationMember)
class ConversationMemberAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'user', 'role', 'joined_at')
    list_filter = ('role',)
    search_fields = ('user__username',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'created_at')
    search_fields = ('body', 'sender__username')
