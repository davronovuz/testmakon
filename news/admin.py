"""
TestMakon.uz - News & Notifications Admin
Professional admin panel for content management
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Q
from django.urls import reverse
from .models import Category, Article, ArticleLike, Notification


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Yangilik kategoriyasi admin"""

    list_display = [
        'icon_preview', 'name', 'color_preview',
        'articles_count', 'order', 'is_active'
    ]
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']

    fieldsets = (
        ('Asosiy', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Vizual', {
            'fields': ('icon', 'color', 'color_preview')
        }),
        ('Sozlamalar', {
            'fields': ('order', 'is_active')
        })
    )

    readonly_fields = ['color_preview']

    @admin.display(description='')
    def icon_preview(self, obj):
        return format_html(
            '<span style="font-size: 24px;">{}</span>',
            obj.icon
        )

    @admin.display(description='Rang')
    def color_preview(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<div style="width: 30px; height: 30px; background-color: {}; '
            'border-radius: 5px; border: 1px solid #ddd;"></div>'
            '<span>{}</span></div>',
            obj.color, obj.color
        )

    @admin.display(description='Maqolalar')
    def articles_count(self, obj):
        count = obj.articles.filter(is_published=True).count()
        return format_html(
            '<strong style="color: #2ecc71;">{}</strong> ta',
            count
        )


class ArticleLikeInline(admin.TabularInline):
    model = ArticleLike
    extra = 0
    readonly_fields = ['user', 'created_at']
    can_delete = False
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Maqola admin"""

    list_display = [
        'title_display', 'type_badge', 'category',
        'author', 'status_badge', 'stats_display',
        'published_at'
    ]
    list_filter = [
        'article_type', 'category', 'is_published',
        'is_featured', 'is_pinned', 'published_at'
    ]
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = [
        'uuid', 'views_count', 'likes_count',
        'created_at', 'updated_at', 'image_preview',
        'engagement_stats'
    ]
    autocomplete_fields = ['author', 'category', 'subject']
    date_hierarchy = 'published_at'
    inlines = [ArticleLikeInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'title', 'slug', 'excerpt')
        }),
        ('Mazmun', {
            'fields': ('content',)
        }),
        ('Turi va kategoriya', {
            'fields': ('article_type', 'category', 'subject')
        }),
        ('Media', {
            'fields': ('featured_image', 'image_preview')
        }),
        ('Muallif', {
            'fields': ('author',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Holat', {
            'fields': (
                'is_published', 'is_featured', 'is_pinned',
                'published_at'
            )
        }),
        ('Statistika', {
            'fields': ('engagement_stats', 'views_count', 'likes_count')
        }),
        ('Vaqtlar', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    actions = ['publish_articles', 'unpublish_articles', 'feature_articles', 'pin_articles']

    @admin.display(description='Maqola')
    def title_display(self, obj):
        badges = []
        if obj.is_pinned:
            badges.append('📌')
        if obj.is_featured:
            badges.append('⭐')

        badge_str = ' '.join(badges)
        return format_html(
            '{} <strong>{}</strong><br><small style="color: #95a5a6;">{}</small>',
            badge_str, obj.title[:60], obj.excerpt[:80] + '...' if len(obj.excerpt) > 80 else obj.excerpt
        )

    @admin.display(description='Turi')
    def type_badge(self, obj):
        colors = {
            'news': '#3498db',
            'announcement': '#e74c3c',
            'tip': '#2ecc71',
            'guide': '#f39c12',
            'update': '#9b59b6'
        }
        icons = {
            'news': '📰',
            'announcement': '📢',
            'tip': '💡',
            'guide': '📖',
            'update': '🔄'
        }
        color = colors.get(obj.article_type, '#95a5a6')
        icon = icons.get(obj.article_type, '📄')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            color, icon, obj.get_article_type_display()
        )

    @admin.display(description='Holat')
    def status_badge(self, obj):
        if not obj.is_published:
            return format_html(
                '<span style="background-color: #95a5a6; color: white; '
                'padding: 3px 8px; border-radius: 3px;">📝 Qoralama</span>'
            )
        return format_html(
            '<span style="background-color: #2ecc71; color: white; '
            'padding: 3px 8px; border-radius: 3px;">✓ Nashr</span>'
        )

    @admin.display(description='Statistika')
    def stats_display(self, obj):
        return format_html(
            '<span style="color: #3498db;">👁 {}</span> | '
            '<span style="color: #e74c3c;">❤ {}</span>',
            obj.views_count, obj.likes_count
        )

    @admin.display(description='Rasm')
    def image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" width="300" style="border-radius: 5px;" />',
                obj.featured_image.url
            )
        return format_html(
            '<div style="width: 300px; height: 200px; background-color: #ecf0f1; '
            'display: flex; align-items: center; justify-content: center; '
            'border-radius: 5px; color: #95a5a6;">Rasm yuklanmagan</div>'
        )

    @admin.display(description='Faollik statistikasi')
    def engagement_stats(self, obj):
        engagement_rate = 0
        if obj.views_count > 0:
            engagement_rate = (obj.likes_count / obj.views_count) * 100

        return format_html(
            '<table style="width: 100%;">'
            '<tr><td><strong>Ko\'rishlar:</strong></td><td style="color: #3498db;">{:,}</td></tr>'
            '<tr><td><strong>Yoqtirishlar:</strong></td><td style="color: #e74c3c;">{:,}</td></tr>'
            '<tr><td><strong>Engagement:</strong></td><td><strong>{:.2f}%</strong></td></tr>'
            '</table>',
            obj.views_count, obj.likes_count, engagement_rate
        )

    # Actions
    @admin.action(description='Nashr qilish')
    def publish_articles(self, request, queryset):
        now = timezone.now()
        updated = queryset.update(
            is_published=True,
            published_at=now
        )
        self.message_user(request, f'{updated} ta maqola nashr qilindi.')

    @admin.action(description='Nashrdan olib tashlash')
    def unpublish_articles(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} ta maqola nashrdan olib tashlandi.')

    @admin.action(description='Tavsiya etish (Featured)')
    def feature_articles(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} ta maqola tavsiya etildi.')

    @admin.action(description='Qadoqlash (Pin)')
    def pin_articles(self, request, queryset):
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} ta maqola qadoqlandi.')


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    """Maqola yoqtirish admin"""

    list_display = ['user', 'article_title', 'created_at']
    list_filter = ['created_at']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number',
        'article__title'
    ]
    readonly_fields = ['created_at']
    autocomplete_fields = ['user', 'article']
    date_hierarchy = 'created_at'

    @admin.display(description='Maqola')
    def article_title(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:news_app_article_change', args=[obj.article.id]),
            obj.article.title[:60]
        )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Bildirishnoma admin"""

    list_display = [
        'user', 'type_badge', 'title_display',
        'status_badge', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'created_at'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number',
        'title', 'message'
    ]
    readonly_fields = ['created_at', 'read_at']
    autocomplete_fields = ['user']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user',)
        }),
        ('Bildirishnoma', {
            'fields': ('notification_type', 'title', 'message')
        }),
        ('Bog\'lanish', {
            'fields': ('link', 'related_id')
        }),
        ('Holat', {
            'fields': ('is_read', 'read_at')
        }),
        ('Vaqt', {
            'fields': ('created_at',)
        })
    )

    actions = ['mark_as_read', 'mark_as_unread', 'send_to_all_users']

    @admin.display(description='Turi')
    def type_badge(self, obj):
        colors = {
            'system': '#95a5a6',
            'news': '#3498db',
            'competition': '#f39c12',
            'battle': '#e74c3c',
            'achievement': '#f1c40f',
            'friend': '#1abc9c',
            'reminder': '#9b59b6'
        }
        icons = {
            'system': '⚙️',
            'news': '📰',
            'competition': '🏆',
            'battle': '⚔️',
            'achievement': '🏅',
            'friend': '👥',
            'reminder': '⏰'
        }
        color = colors.get(obj.notification_type, '#95a5a6')
        icon = icons.get(obj.notification_type, '📬')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{} {}</span>',
            color, icon, obj.get_notification_type_display()
        )

    @admin.display(description='Xabar')
    def title_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: #95a5a6;">{}</small>',
            obj.title,
            obj.message[:100] + '...' if len(obj.message) > 100 else obj.message
        )

    @admin.display(description='Holat', boolean=True)
    def status_badge(self, obj):
        return obj.is_read

    # Actions
    @admin.action(description='O\'qilgan deb belgilash')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(
            is_read=True,
            read_at=timezone.now()
        )
        self.message_user(request, f'{updated} ta bildirishnoma o\'qilgan deb belgilandi.')

    @admin.action(description='O\'qilmagan deb belgilash')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} ta bildirishnoma o\'qilmagan deb belgilandi.')

    @admin.action(description='Barcha foydalanuvchilarga yuborish')
    def send_to_all_users(self, request, queryset):
        from accounts.models import User

        if queryset.count() > 1:
            self.message_user(
                request,
                'Faqat bitta bildirishnomani tanlang!',
                level='ERROR'
            )
            return

        notification = queryset.first()
        users = User.objects.filter(is_active=True)

        notifications = []
        for user in users:
            notifications.append(
                Notification(
                    user=user,
                    notification_type=notification.notification_type,
                    title=notification.title,
                    message=notification.message,
                    link=notification.link,
                    related_id=notification.related_id
                )
            )

        Notification.objects.bulk_create(notifications)
        self.message_user(
            request,
            f'Bildirishnoma {users.count()} ta foydalanuvchiga yuborildi!'
        )


# Custom admin views for statistics
class NewsStatisticsAdmin(admin.ModelAdmin):
    """Yangiliklar statistikasi"""

    change_list_template = 'admin/news_statistics.html'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        # Articles statistics
        total_articles = Article.objects.count()
        published_articles = Article.objects.filter(is_published=True).count()
        draft_articles = total_articles - published_articles

        # Views and likes
        total_views = Article.objects.aggregate(
            total=models.Sum('views_count')
        )['total'] or 0
        total_likes = Article.objects.aggregate(
            total=models.Sum('likes_count')
        )['total'] or 0

        # Top articles
        top_articles = Article.objects.filter(
            is_published=True
        ).order_by('-views_count')[:5]

        # Most liked
        most_liked = Article.objects.filter(
            is_published=True
        ).order_by('-likes_count')[:5]

        # Notifications stats
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        read_rate = 0
        if total_notifications > 0:
            read_rate = ((total_notifications - unread_notifications) / total_notifications) * 100

        extra_context.update({
            'total_articles': total_articles,
            'published_articles': published_articles,
            'draft_articles': draft_articles,
            'total_views': total_views,
            'total_likes': total_likes,
            'top_articles': top_articles,
            'most_liked': most_liked,
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'read_rate': read_rate,
        })

        return super().changelist_view(request, extra_context)


# Admin site customization
admin.site.site_header = 'TestMakon.uz - Yangiliklar va Bildirishnomalar'
admin.site.index_title = 'Kontent boshqaruvi'