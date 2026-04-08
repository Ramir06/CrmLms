from django.contrib import admin
from .models import ChatRoom, ChatMessage, ChatReadStatus, ChatAttachment


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


class ChatAttachmentInline(admin.TabularInline):
    model = ChatAttachment
    extra = 0
    readonly_fields = ['file_size', 'mime_type', 'created_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['author', 'room', 'content_preview', 'is_pinned', 'is_edited', 'is_deleted', 'created_at']
    list_filter = ['is_pinned', 'is_edited', 'is_deleted', 'created_at', 'room']
    search_fields = ['content', 'author__first_name', 'author__last_name', 'author__username']
    readonly_fields = ['created_at', 'updated_at', 'edited_at', 'deleted_at']
    inlines = [ChatAttachmentInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Содержание'


@admin.register(ChatReadStatus)
class ChatReadStatusAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'last_read_message', 'updated_at']
    list_filter = ['room', 'updated_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'room__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ChatAttachment)
class ChatAttachmentAdmin(admin.ModelAdmin):
    list_display = ['filename', 'message', 'file_size_display', 'mime_type', 'created_at']
    list_filter = ['mime_type', 'created_at']
    search_fields = ['filename', 'message__content']
    readonly_fields = ['file_size', 'mime_type', 'created_at', 'updated_at']
    
    def file_size_display(self, obj):
        return obj.file_size_display
    file_size_display.short_description = 'Размер файла'
