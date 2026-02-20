from django import forms
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path
from django.contrib import messages
from .models import Category, Article, ArticleLike, Notification

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'article_type', 'views_count', 'is_published', 'published_at')
    list_filter = ('article_type', 'is_published', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    autocomplete_fields = ['author', 'subject']
    list_editable = ('is_published',)

class BulkNotificationForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        label='Sarlavha',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Bildirishnoma sarlavhasi'})
    )
    message = forms.CharField(
        label='Xabar matni',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Foydalanuvchilarga yuboriladigan xabar...'})
    )
    notification_type = forms.ChoiceField(
        choices=Notification.NOTIFICATION_TYPES,
        label='Bildirishnoma turi',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    link = forms.CharField(
        max_length=500,
        required=False,
        label='Havola (ixtiyoriy)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '/competitions/ yoki https://...'})
    )
    only_active = forms.BooleanField(
        required=False,
        initial=True,
        label='Faqat faol foydalanuvchilarga',
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__first_name', 'user__phone_number')
    date_hierarchy = 'created_at'

    def get_urls(self):
        custom_urls = [
            path(
                'send-bulk/',
                self.admin_site.admin_view(self.send_bulk_view),
                name='notification_send_bulk',
            ),
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['bulk_url'] = 'send-bulk/'
        return super().changelist_view(request, extra_context=extra_context)

    def send_bulk_view(self, request):
        from accounts.models import User

        if request.method == 'POST':
            form = BulkNotificationForm(request.POST)
            if form.is_valid():
                qs = User.objects.all()
                if form.cleaned_data.get('only_active'):
                    qs = qs.filter(is_active=True)

                notifs = [
                    Notification(
                        user=user,
                        title=form.cleaned_data['title'],
                        message=form.cleaned_data['message'],
                        notification_type=form.cleaned_data['notification_type'],
                        link=form.cleaned_data.get('link', ''),
                    )
                    for user in qs
                ]
                Notification.objects.bulk_create(notifs, batch_size=500)
                count = len(notifs)
                self.message_user(
                    request,
                    f'✅ {count} ta foydalanuvchiga bildirishnoma muvaffaqiyatli yuborildi!',
                    messages.SUCCESS
                )
                return redirect('../')
        else:
            form = BulkNotificationForm()

        from accounts.models import User
        total_users = User.objects.filter(is_active=True).count()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Barcha foydalanuvchilarga xabar yuborish',
            'form': form,
            'opts': self.model._meta,
            'total_users': total_users,
        }
        return render(request, 'admin/news/send_bulk_notification.html', context)

admin.site.register(ArticleLike)



from .models import SystemBanner

@admin.register(SystemBanner)
class SystemBannerAdmin(admin.ModelAdmin):
    list_display = ['message', 'banner_type', 'is_active', 'is_scrolling', 'order', 'created_at']
    list_filter = ['banner_type', 'is_active', 'is_scrolling']
    list_editable = ['is_active', 'order']
    search_fields = ['message']
    ordering = ['order', '-created_at']