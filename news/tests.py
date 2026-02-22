"""
TestMakon.uz - News App Tests
Modellar va viewlar uchun to'liq testlar
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import Category, Article, ArticleLike, Notification, SystemBanner

User = get_user_model()


# ============================================================
# YORDAMCHI FUNKSIYALAR
# ============================================================

def make_user(username='testuser', password='pass1234'):
    return User.objects.create_user(username=username, password=password)


def make_category(**kwargs):
    defaults = {'name': 'Test Kategoriya', 'slug': 'test-kategoriya'}
    defaults.update(kwargs)
    return Category.objects.create(**defaults)


def make_article(author, category=None, **kwargs):
    defaults = {
        'title': 'Test Maqola',
        'slug': 'test-maqola',
        'excerpt': 'Qisqa tavsif',
        'content': 'Maqola matni',
        'article_type': 'news',
        'is_published': True,
        'published_at': timezone.now(),
        'author': author,
        'category': category,
    }
    defaults.update(kwargs)
    return Article.objects.create(**defaults)


# ============================================================
# MODEL TESTLAR
# ============================================================

class CategoryModelTest(TestCase):

    def test_create(self):
        cat = make_category()
        self.assertEqual(cat.name, 'Test Kategoriya')
        self.assertTrue(cat.is_active)

    def test_str(self):
        cat = make_category(name='DTM Yangiliklari', slug='dtm')
        self.assertEqual(str(cat), 'DTM Yangiliklari')

    def test_default_icon_and_color(self):
        cat = make_category()
        self.assertEqual(cat.icon, '📰')
        self.assertEqual(cat.color, '#3498db')

    def test_ordering_by_order_then_name(self):
        make_category(name='Z Fan', slug='z-fan', order=2)
        make_category(name='A Fan', slug='a-fan', order=1)
        names = list(Category.objects.values_list('name', flat=True))
        self.assertEqual(names[0], 'A Fan')
        self.assertEqual(names[1], 'Z Fan')


class ArticleModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.category = make_category()

    def test_create(self):
        article = make_article(self.user, self.category)
        self.assertEqual(article.title, 'Test Maqola')
        self.assertTrue(article.is_published)
        self.assertEqual(article.views_count, 0)
        self.assertEqual(article.likes_count, 0)

    def test_str(self):
        article = make_article(self.user, title='Yangi Maqola', slug='yangi-maqola')
        self.assertEqual(str(article), 'Yangi Maqola')

    def test_increment_views(self):
        article = make_article(self.user)
        article.increment_views()
        article.refresh_from_db()
        self.assertEqual(article.views_count, 1)

    def test_increment_views_multiple(self):
        article = make_article(self.user)
        for _ in range(5):
            article.increment_views()
        article.refresh_from_db()
        self.assertEqual(article.views_count, 5)

    def test_unpublished_excluded_from_filter(self):
        make_article(self.user, is_published=False, slug='unpublished')
        make_article(self.user, is_published=True, slug='published')
        self.assertEqual(Article.objects.filter(is_published=True).count(), 1)

    def test_uuid_is_unique(self):
        a1 = make_article(self.user, slug='art-1')
        a2 = make_article(self.user, slug='art-2')
        self.assertNotEqual(a1.uuid, a2.uuid)

    def test_category_nullable(self):
        article = make_article(self.user, category=None)
        self.assertIsNone(article.category)

    def test_is_featured_default_false(self):
        self.assertFalse(make_article(self.user).is_featured)

    def test_is_pinned_default_false(self):
        self.assertFalse(make_article(self.user).is_pinned)

    def test_all_article_types_valid(self):
        for i, (type_val, _) in enumerate(Article.ARTICLE_TYPES):
            a = make_article(self.user, slug=f'type-{i}', article_type=type_val)
            self.assertEqual(a.article_type, type_val)


class ArticleLikeModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.article = make_article(self.user)

    def test_create_like(self):
        like = ArticleLike.objects.create(article=self.article, user=self.user)
        self.assertEqual(like.article, self.article)
        self.assertEqual(like.user, self.user)

    def test_unique_together(self):
        """Bir foydalanuvchi bir maqolani faqat bir marta yoqtira oladi"""
        ArticleLike.objects.create(article=self.article, user=self.user)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ArticleLike.objects.create(article=self.article, user=self.user)

    def test_different_users_can_like_same_article(self):
        user2 = make_user(username='user2')
        ArticleLike.objects.create(article=self.article, user=self.user)
        ArticleLike.objects.create(article=self.article, user=user2)
        self.assertEqual(ArticleLike.objects.filter(article=self.article).count(), 2)


class NotificationModelTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_create_defaults(self):
        n = Notification.objects.create(
            user=self.user,
            notification_type='system',
            title='Test',
            message='Xabar matni',
        )
        self.assertFalse(n.is_read)
        self.assertIsNone(n.read_at)

    def test_str(self):
        n = Notification.objects.create(
            user=self.user,
            notification_type='news',
            title='Yangi xabar',
            message='Xabar',
        )
        self.assertIn('Yangi xabar', str(n))
        self.assertIn(self.user.username, str(n))

    def test_mark_read(self):
        n = Notification.objects.create(
            user=self.user, notification_type='system', title='Test', message='x'
        )
        n.is_read = True
        n.read_at = timezone.now()
        n.save()
        n.refresh_from_db()
        self.assertTrue(n.is_read)
        self.assertIsNotNone(n.read_at)

    def test_ordering_newest_first(self):
        n1 = Notification.objects.create(
            user=self.user, notification_type='system', title='Birinchi', message='x'
        )
        n2 = Notification.objects.create(
            user=self.user, notification_type='system', title='Ikkinchi', message='x'
        )
        notifications = list(Notification.objects.filter(user=self.user))
        self.assertEqual(notifications[0], n2)
        self.assertEqual(notifications[1], n1)


class SystemBannerModelTest(TestCase):

    def test_create_defaults(self):
        banner = SystemBanner.objects.create(
            message='Yangi imtihon boshlandi!',
            banner_type='info',
        )
        self.assertTrue(banner.is_active)
        self.assertTrue(banner.is_scrolling)
        self.assertEqual(banner.scroll_speed, 15)

    def test_str_truncated_to_50(self):
        banner = SystemBanner.objects.create(message='A' * 100, banner_type='info')
        self.assertEqual(len(str(banner)), 50)

    def test_str_short_message(self):
        banner = SystemBanner.objects.create(message='Qisqa xabar', banner_type='info')
        self.assertEqual(str(banner), 'Qisqa xabar')


# ============================================================
# VIEW TESTLAR
# ============================================================

class NewsListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('news:news_list')

    def test_get_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_only_published_articles_shown(self):
        make_article(self.user, slug='pub', is_published=True)
        make_article(self.user, slug='unpub', is_published=False)
        response = self.client.get(self.url)
        for a in response.context['articles']:
            self.assertTrue(a.is_published)

    def test_filter_by_type(self):
        make_article(self.user, slug='news1', article_type='news')
        make_article(self.user, slug='tip1', article_type='tip')
        response = self.client.get(self.url + '?type=tip')
        for a in response.context['articles']:
            self.assertEqual(a.article_type, 'tip')

    def test_context_keys_present(self):
        response = self.client.get(self.url)
        for key in ('articles', 'categories', 'featured'):
            self.assertIn(key, response.context)

    def test_featured_only_featured_articles(self):
        make_article(self.user, slug='feat', is_featured=True)
        make_article(self.user, slug='nofeat', is_featured=False)
        response = self.client.get(self.url)
        for a in response.context['featured']:
            self.assertTrue(a.is_featured)

    def test_featured_max_3(self):
        for i in range(5):
            make_article(self.user, slug=f'feat-{i}', is_featured=True)
        response = self.client.get(self.url)
        self.assertLessEqual(len(response.context['featured']), 3)


class CategoryDetailViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.category = make_category(slug='matematika')
        self.url = reverse('news:category_detail', kwargs={'slug': 'matematika'})

    def test_get_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_inactive_category_404(self):
        make_category(name='Yopiq', slug='yopiq', is_active=False)
        url = reverse('news:category_detail', kwargs={'slug': 'yopiq'})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_wrong_slug_404(self):
        url = reverse('news:category_detail', kwargs={'slug': 'mavjud-emas'})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_context_category_correct(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context['category'], self.category)

    def test_only_published_articles(self):
        make_article(self.user, self.category, slug='pub')
        make_article(self.user, self.category, slug='unpub', is_published=False)
        response = self.client.get(self.url)
        for a in response.context['articles']:
            self.assertTrue(a.is_published)

    def test_other_category_articles_not_shown(self):
        other_cat = make_category(name='Boshqa', slug='boshqa')
        make_article(self.user, self.category, slug='mine')
        make_article(self.user, other_cat, slug='other')
        response = self.client.get(self.url)
        for a in response.context['articles']:
            self.assertEqual(a.category, self.category)


class ArticleDetailViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.article = make_article(self.user, slug='test-maqola')
        self.url = reverse('news:article_detail', kwargs={'slug': 'test-maqola'})

    def test_get_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_unpublished_returns_404(self):
        make_article(self.user, slug='yashirin', is_published=False)
        url = reverse('news:article_detail', kwargs={'slug': 'yashirin'})
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_views_incremented_on_visit(self):
        self.client.get(self.url)
        self.article.refresh_from_db()
        self.assertEqual(self.article.views_count, 1)

    def test_views_incremented_each_visit(self):
        self.client.get(self.url)
        self.client.get(self.url)
        self.article.refresh_from_db()
        self.assertEqual(self.article.views_count, 2)

    def test_is_liked_false_for_anonymous(self):
        self.assertFalse(self.client.get(self.url).context['is_liked'])

    def test_is_liked_false_for_user_who_hasnt_liked(self):
        self.client.login(username='testuser', password='pass1234')
        self.assertFalse(self.client.get(self.url).context['is_liked'])

    def test_is_liked_true_for_user_who_liked(self):
        ArticleLike.objects.create(article=self.article, user=self.user)
        self.client.login(username='testuser', password='pass1234')
        self.assertTrue(self.client.get(self.url).context['is_liked'])

    def test_related_excludes_current_article(self):
        category = make_category()
        self.article.category = category
        self.article.save()
        make_article(self.user, category, slug='related-1')
        response = self.client.get(self.url)
        self.assertNotIn(self.article, list(response.context['related']))

    def test_context_has_article(self):
        self.assertEqual(self.client.get(self.url).context['article'], self.article)


class ArticleLikeViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.article = make_article(self.user, slug='liked-maqola')
        self.url = reverse('news:article_like', kwargs={'slug': 'liked-maqola'})

    def test_anonymous_redirected_to_login(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url.lower())

    def test_like_creates_object(self):
        self.client.login(username='testuser', password='pass1234')
        self.client.post(self.url)
        self.assertTrue(ArticleLike.objects.filter(article=self.article, user=self.user).exists())

    def test_like_increments_count(self):
        self.client.login(username='testuser', password='pass1234')
        self.client.post(self.url)
        self.article.refresh_from_db()
        self.assertEqual(self.article.likes_count, 1)

    def test_unlike_removes_object(self):
        ArticleLike.objects.create(article=self.article, user=self.user)
        self.article.likes_count = 1
        self.article.save()
        self.client.login(username='testuser', password='pass1234')
        self.client.post(self.url)
        self.assertFalse(ArticleLike.objects.filter(article=self.article, user=self.user).exists())

    def test_unlike_decrements_count(self):
        ArticleLike.objects.create(article=self.article, user=self.user)
        self.article.likes_count = 1
        self.article.save()
        self.client.login(username='testuser', password='pass1234')
        self.client.post(self.url)
        self.article.refresh_from_db()
        self.assertEqual(self.article.likes_count, 0)

    def test_ajax_like_returns_json(self):
        self.client.login(username='testuser', password='pass1234')
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['liked'])
        self.assertEqual(data['count'], 1)

    def test_ajax_unlike_returns_json(self):
        ArticleLike.objects.create(article=self.article, user=self.user)
        self.article.likes_count = 1
        self.article.save()
        self.client.login(username='testuser', password='pass1234')
        response = self.client.post(self.url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        data = response.json()
        self.assertFalse(data['liked'])
        self.assertEqual(data['count'], 0)


class TipsListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('news:tips_list')

    def test_get_200(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_only_tips_type_shown(self):
        make_article(self.user, slug='tip1', article_type='tip')
        make_article(self.user, slug='news1', article_type='news')
        response = self.client.get(self.url)
        for t in response.context['tips']:
            self.assertEqual(t.article_type, 'tip')

    def test_unpublished_tips_not_shown(self):
        make_article(self.user, slug='tip-pub', article_type='tip', is_published=True)
        make_article(self.user, slug='tip-unpub', article_type='tip', is_published=False)
        response = self.client.get(self.url)
        for t in response.context['tips']:
            self.assertTrue(t.is_published)

    def test_context_has_subjects(self):
        self.assertIn('subjects', self.client.get(self.url).context)


class NotificationsListViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('news:notifications_list')

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_logged_in_200(self):
        self.client.login(username='testuser', password='pass1234')
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_only_own_notifications(self):
        other = make_user(username='other')
        Notification.objects.create(user=self.user, notification_type='system', title='Meniki', message='x')
        Notification.objects.create(user=other, notification_type='system', title='Boshqaniki', message='x')
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(self.url)
        for n in response.context['notifications']:
            self.assertEqual(n.user, self.user)

    def test_max_50_returned(self):
        for i in range(60):
            Notification.objects.create(
                user=self.user, notification_type='system', title=f'x{i}', message='x'
            )
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(self.url)
        self.assertLessEqual(len(response.context['notifications']), 50)


class NotificationMarkReadViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.notif = Notification.objects.create(
            user=self.user, notification_type='system', title='Test', message='x'
        )
        self.url = reverse('news:notification_mark_read', kwargs={'id': self.notif.id})

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_marks_as_read(self):
        self.client.login(username='testuser', password='pass1234')
        self.client.get(self.url)
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.is_read)
        self.assertIsNotNone(self.notif.read_at)

    def test_other_users_notification_404(self):
        other = make_user(username='other')
        n = Notification.objects.create(user=other, notification_type='system', title='x', message='x')
        url = reverse('news:notification_mark_read', kwargs={'id': n.id})
        self.client.login(username='testuser', password='pass1234')
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_with_link_redirects_to_link(self):
        self.notif.link = '/some/path/'
        self.notif.save()
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(self.url)
        self.assertRedirects(response, '/some/path/', fetch_redirect_response=False)

    def test_without_link_redirects_to_notifications_list(self):
        self.client.login(username='testuser', password='pass1234')
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse('news:notifications_list'))


class NotificationsMarkAllReadViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('news:notifications_mark_all_read')

    def test_anonymous_redirected(self):
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_marks_all_as_read(self):
        for i in range(3):
            Notification.objects.create(
                user=self.user, notification_type='system', title=f'x{i}', message='x'
            )
        self.client.login(username='testuser', password='pass1234')
        self.client.get(self.url)
        self.assertEqual(Notification.objects.filter(user=self.user, is_read=False).count(), 0)

    def test_does_not_affect_other_users(self):
        other = make_user(username='other')
        Notification.objects.create(user=other, notification_type='system', title='x', message='x')
        self.client.login(username='testuser', password='pass1234')
        self.client.get(self.url)
        self.assertEqual(Notification.objects.filter(user=other, is_read=False).count(), 1)


class ApiUnreadCountViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.url = reverse('news:api_unread_count')

    def test_anonymous_returns_zero(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 0)

    def test_returns_correct_unread_count(self):
        Notification.objects.create(user=self.user, notification_type='system', title='1', message='x', is_read=False)
        Notification.objects.create(user=self.user, notification_type='system', title='2', message='x', is_read=False)
        Notification.objects.create(user=self.user, notification_type='system', title='3', message='x', is_read=True)
        self.client.login(username='testuser', password='pass1234')
        self.assertEqual(self.client.get(self.url).json()['count'], 2)

    def test_response_is_json(self):
        response = self.client.get(self.url)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('count', response.json())

    def test_read_notifications_not_counted(self):
        for i in range(3):
            Notification.objects.create(
                user=self.user, notification_type='system',
                title=f'x{i}', message='x', is_read=True
            )
        self.client.login(username='testuser', password='pass1234')
        self.assertEqual(self.client.get(self.url).json()['count'], 0)
