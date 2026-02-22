from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from .models import PhoneVerification, Friendship, UserActivity

User = get_user_model()

class UserModelTest(TestCase):
    """User modeli uchun testlar"""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='strong_password',
            first_name='Test',
            last_name='User'
        )

    def test_create_user(self):
        """Foydalanuvchi yaratishni tekshirish"""
        self.assertEqual(self.user.phone_number, '+998901234567')
        self.assertTrue(self.user.check_password('strong_password'))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)

    def test_create_superuser(self):
        """Superuser yaratishni tekshirish"""
        admin = User.objects.create_superuser(
            phone_number='+998909999999',
            password='admin_password',
            first_name='Admin'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_gamification_logic(self):
        """XP va Level tizimini tekshirish"""
        # Boshlang'ich holat
        self.assertEqual(self.user.xp_points, 0)
        self.assertEqual(self.user.level, 'beginner')

        # XP qo'shish (500 XP = elementary)
        self.user.add_xp(600)
        self.assertEqual(self.user.xp_points, 600)
        self.assertEqual(self.user.level, 'elementary')

        # Yana XP qo'shish (2000 XP = intermediate)
        self.user.add_xp(1500)  # Total 2100
        self.assertEqual(self.user.level, 'intermediate')


class AuthenticationViewTest(TestCase):
    """Ro'yxatdan o'tish va kirish viewlari uchun testlar"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')

        # Test user for login
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='password123',
            first_name='Login',
            last_name='Test'
        )

    def test_register_view_get(self):
        """Register sahifasi ochilishini tekshirish"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_view_post_success(self):
        """Muvaffaqiyatli ro'yxatdan o'tish"""
        data = {
            'phone_number': '901112233',  # Prefikssiz
            'first_name': 'New',
            'last_name': 'User',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = self.client.post(self.register_url, data)

        # Muvaffaqiyatli bo'lsa testlar ro'yxatiga yo'naltiradi
        self.assertRedirects(response, reverse('tests_app:tests_list'))

        # User yaratilganini tekshirish
        self.assertTrue(User.objects.filter(phone_number='+998901112233').exists())

        # Verification code yaratilganini tekshirish
        self.assertTrue(PhoneVerification.objects.filter(phone_number='+998901112233').exists())

    def test_login_view_success(self):
        """To'g'ri ma'lumotlar bilan kirish"""
        data = {
            'phone_number': '+998901234567',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data)

        # Tizimga kirganini tekshirish
        self.assertRedirects(response, reverse('tests_app:tests_list'))
        # Session user id si to'g'riligini tekshirish
        self.assertEqual(str(self.client.session['_auth_user_id']), str(self.user.id))

    def test_login_view_fail(self):
        """Noto'g'ri parol bilan kirish"""
        data = {
            'phone_number': '+998901234567',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)

        # Sahifada qolishi kerak (200 OK) va form error bo'lishi kerak
        self.assertEqual(response.status_code, 200)
        # Authentication failed message check is tricky directly, usually checked via messages context

    def test_logout_view(self):
        """Chiqish funksiyasi"""
        self.client.login(phone_number='+998901234567', password='password123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('core:home'))

        # Session tozalanganini tekshirish
        with self.assertRaises(KeyError):
            _ = self.client.session['_auth_user_id']


class FriendshipTest(TestCase):
    """Do'stlik tizimi testlari"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            phone_number='+998901111111',
            password='password123',
            first_name='User1'
        )
        self.user2 = User.objects.create_user(
            phone_number='+998902222222',
            password='password123',
            first_name='User2'
        )
        # User1 sifatida login qilish
        self.client.force_login(self.user1)

    def test_send_friend_request(self):
        """Do'stlik so'rovi yuborish"""
        url = reverse('accounts:friend_add', args=[self.user2.id])
        response = self.client.get(url)

        self.assertRedirects(response, reverse('accounts:friends_list'))

        # Baza tekshirish
        friendship = Friendship.objects.filter(from_user=self.user1, to_user=self.user2).first()
        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.status, 'pending')

    def test_accept_friend_request(self):
        """So'rovni qabul qilish"""
        # Avval so'rov yaratamiz (User2 -> User1)
        friendship = Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )

        url = reverse('accounts:friend_accept', args=[friendship.id])
        response = self.client.get(url)

        # Bazani yangilab tekshiramiz
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')

class ProfileViewTest(TestCase):
    """Profil sahifasi testlari"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='password123',
            first_name='Profile',
            last_name='Test'
        )
        self.profile_url = reverse('accounts:profile')

    def test_profile_access_unauthorized(self):
        """Login qilmasdan kirish (Redirect bo'lishi kerak)"""
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.profile_url}")

    def test_profile_access_authorized(self):
        """Login qilib kirish"""
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertEqual(response.context['profile_user'], self.user)

    def test_public_profile(self):
        """Boshqa odamning profilini ko'rish"""
        other_user = User.objects.create_user(
            phone_number='+998908888888',
            password='password123',
            first_name='Other'
        )
        url = reverse('accounts:profile_public', args=[other_user.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile_user'], other_user)
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from .models import PhoneVerification, Friendship, UserActivity, UserBadge, Badge

User = get_user_model()

class UserModelTest(TestCase):
    """User modeli uchun testlar"""

    def setUp(self):
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='strong_password',
            first_name='Test',
            last_name='User'
        )

    def test_create_user(self):
        """Foydalanuvchi yaratishni tekshirish"""
        self.assertEqual(self.user.phone_number, '+998901234567')
        self.assertTrue(self.user.check_password('strong_password'))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)

    def test_create_superuser(self):
        """Superuser yaratishni tekshirish"""
        admin = User.objects.create_superuser(
            phone_number='+998909999999',
            password='admin_password',
            first_name='Admin'
        )
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_gamification_logic(self):
        """XP va Level tizimini tekshirish"""
        # Boshlang'ich holat
        self.assertEqual(self.user.xp_points, 0)
        self.assertEqual(self.user.level, 'beginner')

        # XP qo'shish (500 XP = elementary)
        self.user.add_xp(600)
        self.assertEqual(self.user.xp_points, 600)
        self.assertEqual(self.user.level, 'elementary')

        # Yana XP qo'shish (2000 XP = intermediate)
        self.user.add_xp(1500)  # Total 2100
        self.assertEqual(self.user.level, 'intermediate')


class AuthenticationViewTest(TestCase):
    """Ro'yxatdan o'tish va kirish viewlari uchun testlar"""

    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
        self.login_url = reverse('accounts:login')
        self.logout_url = reverse('accounts:logout')

        # Test user for login
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='password123',
            first_name='Login',
            last_name='Test'
        )

    def test_register_view_get(self):
        """Register sahifasi ochilishini tekshirish"""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_register_view_post_success(self):
        """Muvaffaqiyatli ro'yxatdan o'tish"""
        data = {
            'phone_number': '901112233',  # Prefikssiz
            'first_name': 'New',
            'last_name': 'User',
            'password': 'password123',
            'password_confirm': 'password123'
        }
        response = self.client.post(self.register_url, data)

        # Muvaffaqiyatli bo'lsa testlar ro'yxatiga yo'naltiradi
        self.assertRedirects(response, reverse('tests_app:tests_list'))

        # User yaratilganini tekshirish
        self.assertTrue(User.objects.filter(phone_number='+998901112233').exists())

        # Verification code yaratilganini tekshirish
        self.assertTrue(PhoneVerification.objects.filter(phone_number='+998901112233').exists())

    def test_login_view_success(self):
        """To'g'ri ma'lumotlar bilan kirish"""
        data = {
            'phone_number': '+998901234567',
            'password': 'password123'
        }
        response = self.client.post(self.login_url, data)

        # Tizimga kirganini tekshirish
        self.assertRedirects(response, reverse('tests_app:tests_list'))
        # Session user id si to'g'riligini tekshirish
        self.assertEqual(str(self.client.session['_auth_user_id']), str(self.user.id))

    def test_login_view_fail(self):
        """Noto'g'ri parol bilan kirish"""
        data = {
            'phone_number': '+998901234567',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data)

        # Sahifada qolishi kerak (200 OK) va form error bo'lishi kerak
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        """Chiqish funksiyasi"""
        self.client.login(phone_number='+998901234567', password='password123')
        response = self.client.get(self.logout_url)
        self.assertRedirects(response, reverse('core:home'))

        # Session tozalanganini tekshirish
        with self.assertRaises(KeyError):
            _ = self.client.session['_auth_user_id']


class FriendshipTest(TestCase):
    """Do'stlik tizimi testlari"""

    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            phone_number='+998901111111',
            password='password123',
            first_name='User1'
        )
        self.user2 = User.objects.create_user(
            phone_number='+998902222222',
            password='password123',
            first_name='User2'
        )
        # User1 sifatida login qilish
        self.client.force_login(self.user1)

    def test_send_friend_request(self):
        """Do'stlik so'rovi yuborish"""
        url = reverse('accounts:friend_add', args=[self.user2.id])
        response = self.client.get(url)

        self.assertRedirects(response, reverse('accounts:friends_list'))

        # Baza tekshirish
        friendship = Friendship.objects.filter(from_user=self.user1, to_user=self.user2).first()
        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.status, 'pending')

    def test_accept_friend_request(self):
        """So'rovni qabul qilish"""
        # Avval so'rov yaratamiz (User2 -> User1)
        friendship = Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user1,
            status='pending'
        )

        # User1 sifatida (qabul qiluvchi) so'rovni qabul qilamiz
        url = reverse('accounts:friend_accept', args=[friendship.id])
        response = self.client.get(url)

        # Bazani yangilab tekshiramiz
        friendship.refresh_from_db()
        self.assertEqual(friendship.status, 'accepted')


class ProfileViewTest(TestCase):
    """Profil sahifasi testlari"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='password123',
            first_name='Profile',
            last_name='Test'
        )
        self.profile_url = reverse('accounts:profile')

    def test_profile_access_unauthorized(self):
        """Login qilmasdan kirish (Redirect bo'lishi kerak)"""
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={self.profile_url}")

    def test_profile_access_authorized(self):
        """Login qilib kirish"""
        self.client.force_login(self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertEqual(response.context['profile_user'], self.user)

    def test_public_profile(self):
        """Boshqa odamning profilini ko'rish"""
        other_user = User.objects.create_user(
            phone_number='+998908888888',
            password='password123',
            first_name='Other'
        )
        url = reverse('accounts:profile_public', args=[other_user.uuid])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['profile_user'], other_user)
