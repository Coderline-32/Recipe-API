from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Message, Follow, Favorite, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User model admin with extended functionality.
    """
    list_display = (
        'username',
        'email',
        'full_name',
        'profile_picture_thumbnail',
        'follower_count_display',
        'following_count_display',
        'created_at_short',
        'is_active',
    )
    list_filter = (
        'is_active',
        'is_staff',
        'is_superuser',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'bio',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
        'profile_picture_preview',
        'follower_count_display',
        'following_count_display',
        'favorites_count_display',
        'followers_list',
        'following_list',
    )

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'bio', 'profile_picture', 'profile_picture_preview', 'social_links')
        }),
        ('Statistics', {
            'fields': ('follower_count_display', 'following_count_display', 'favorites_count_display'),
            'classes': ('collapse',)
        }),
        ('Relationships', {
            'fields': ('followers_list', 'following_list'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['export_user_data', 'deactivate_users']

    def profile_picture_thumbnail(self, obj):
        """Display profile picture thumbnail in list view."""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; border-radius: 50%;" />',
                obj.profile_picture.url
            )
        return '—'
    profile_picture_thumbnail.short_description = 'Profile Picture'

    def profile_picture_preview(self, obj):
        """Display larger profile picture preview in detail view."""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 10px;" />',
                obj.profile_picture.url
            )
        return 'No profile picture'
    profile_picture_preview.short_description = 'Profile Picture Preview'

    def full_name(self, obj):
        """Display user's full name."""
        return obj.get_full_name() or '—'
    full_name.short_description = 'Full Name'

    def follower_count_display(self, obj):
        """Display follower count."""
        count = obj.get_follower_count()
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    follower_count_display.short_description = 'Followers'

    def following_count_display(self, obj):
        """Display following count."""
        count = obj.get_following_count()
        return format_html(
            '<span style="background-color: #f3e5f5; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    following_count_display.short_description = 'Following'

    def favorites_count_display(self, obj):
        """Display favorites count."""
        count = obj.get_favorites_count()
        return format_html(
            '<span style="background-color: #fff3e0; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    favorites_count_display.short_description = 'Favorites'

    def created_at_short(self, obj):
        """Display created_at in short format."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = 'Joined'

    def followers_list(self, obj):
        """Display list of followers."""
        followers = obj.followers.all()[:10]
        if not followers:
            return 'No followers'
        follower_list = ', '.join([f.username for f in followers])
        if obj.followers.count() > 10:
            follower_list += f', ... and {obj.followers.count() - 10} more'
        return follower_list
    followers_list.short_description = 'Followers (first 10)'

    def following_list(self, obj):
        """Display list of users being followed."""
        following = obj.follows.all()[:10]
        if not following:
            return 'Not following anyone'
        following_list = ', '.join([u.username for u in following])
        if obj.follows.count() > 10:
            following_list += f', ... and {obj.follows.count() - 10} more'
        return following_list
    following_list.short_description = 'Following (first 10)'

    def export_user_data(self, request, queryset):
        """Admin action to export user data."""
        import json
        from django.http import HttpResponse

        data = []
        for user in queryset:
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.get_full_name(),
                'bio': user.bio,
                'followers': user.get_follower_count(),
                'following': user.get_following_count(),
                'favorites': user.get_favorites_count(),
                'created_at': user.created_at.isoformat(),
            }
            data.append(user_data)

        response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="users_export.json"'
        return response
    export_user_data.short_description = 'Export selected users data'

    def deactivate_users(self, request, queryset):
        """Admin action to deactivate users."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} users have been deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Admin for Follow relationships."""
    list_display = ('follower', 'following', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('follower__username', 'following__username')
    readonly_fields = ('created_at',)
    raw_id_fields = ('follower', 'following')

    fieldsets = (
        (None, {'fields': ('follower', 'following')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin for private messages."""
    list_display = ('sender', 'receiver', 'is_read', 'created_at_short', 'content_preview')
    list_filter = ('is_read', 'created_at', 'sender', 'receiver')
    search_fields = ('sender__username', 'receiver__username', 'content')
    readonly_fields = ('created_at', 'updated_at', 'read_at')
    raw_id_fields = ('sender', 'receiver')

    fieldsets = (
        ('Message Details', {'fields': ('sender', 'receiver', 'content')}),
        ('Status', {'fields': ('is_read', 'read_at')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    def content_preview(self, obj):
        """Display truncated message content."""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

    def created_at_short(self, obj):
        """Display created_at in short format."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = 'Date'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Admin for favorite recipes."""
    list_display = ('user', 'recipe', 'created_at_short')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'recipe__title')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'recipe')

    fieldsets = (
        (None, {'fields': ('user', 'recipe')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def created_at_short(self, obj):
        """Display created_at in short format."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = 'Added'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for notifications."""
    list_display = ('user', 'notification_type', 'is_read', 'actor', 'created_at_short', 'description_preview')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'actor__username', 'description')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'actor')

    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'notification_type', 'actor', 'description')
        }),
        ('Related Content', {
            'fields': ('content_type', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Status', {'fields': ('is_read', 'read_at')}),
        ('Timestamps', {'fields': ('created_at',), 'classes': ('collapse',)}),
    )

    def description_preview(self, obj):
        """Display truncated description."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'

    def created_at_short(self, obj):
        """Display created_at in short format."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_short.short_description = 'Date'