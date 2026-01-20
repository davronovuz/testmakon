"""
TestMakon.uz - Accounts Views
Authentication, profile, friends
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import random

from .models import User, Friendship, UserActivity, PhoneVerification, Badge, UserBadge


def register(request):
    """Ro'yxatdan o'tish"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        # Validation
        if not phone_number.startswith('+998'):
            phone_number = '+998' + phone_number.lstrip('0')

        if User.objects.filter(phone_number=phone_number).exists():
            messages.error(request, "Bu telefon raqam allaqachon ro'yxatdan o'tgan")
            return render(request, 'accounts/register.html')

        if password != password_confirm:
            messages.error(request, "Parollar mos kelmadi")
            return render(request, 'accounts/register.html')

        if len(password) < 6:
            messages.error(request, "Parol kamida 6 ta belgidan iborat bo'lishi kerak")
            return render(request, 'accounts/register.html')

        # Create user
        user = User.objects.create_user(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        # Generate verification code
        code = str(random.randint(100000, 999999))
        PhoneVerification.objects.create(
            phone_number=phone_number,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=5)
        )

        # TODO: Send SMS with code
        # For now, we'll just log in the user

        login(request, user)

        # Log activity
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description='Ro\'yxatdan o\'tdi'
        )

        messages.success(request, f"Xush kelibsiz, {first_name}!")
        return redirect('core:dashboard')

    return render(request, 'accounts/register.html')


def login_view(request):
    """Kirish"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        # Format phone number
        if not phone_number.startswith('+998'):
            phone_number = '+998' + phone_number.lstrip('0')

        user = authenticate(request, phone_number=phone_number, password=password)

        if user is not None:
            login(request, user)

            # Remember me
            if not remember:
                request.session.set_expiry(0)

            # Update streak
            user.update_streak()

            # Log activity
            UserActivity.objects.create(
                user=user,
                activity_type='login',
                description='Tizimga kirdi'
            )

            messages.success(request, f"Xush kelibsiz, {user.first_name}!")

            # Redirect to next or dashboard
            next_url = request.GET.get('next', 'core:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Telefon raqam yoki parol noto'g'ri")

    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Chiqish"""
    logout(request)
    messages.info(request, "Tizimdan chiqdingiz")
    return redirect('core:home')


def verify_phone(request):
    """Telefon tasdiqlash"""
    if request.method == 'POST':
        code = request.POST.get('code')
        phone_number = request.user.phone_number if request.user.is_authenticated else request.POST.get('phone_number')

        verification = PhoneVerification.objects.filter(
            phone_number=phone_number,
            code=code,
            is_used=False
        ).first()

        if verification and verification.is_valid:
            verification.is_used = True
            verification.save()

            if request.user.is_authenticated:
                request.user.is_phone_verified = True
                request.user.save()
                messages.success(request, "Telefon raqamingiz tasdiqlandi!")
                return redirect('core:dashboard')
        else:
            messages.error(request, "Kod noto'g'ri yoki muddati o'tgan")

    return render(request, 'accounts/verify_phone.html')


def resend_code(request):
    """Kodni qayta yuborish"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        # Check rate limit
        recent = PhoneVerification.objects.filter(
            phone_number=phone_number,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).exists()

        if recent:
            messages.error(request, "Iltimos, 1 daqiqa kuting")
            return redirect('accounts:verify_phone')

        # Generate new code
        code = str(random.randint(100000, 999999))
        PhoneVerification.objects.create(
            phone_number=phone_number,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=5)
        )

        # TODO: Send SMS
        messages.success(request, "Yangi kod yuborildi")

    return redirect('accounts:verify_phone')


def forgot_password(request):
    """Parolni unutdim"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        if not phone_number.startswith('+998'):
            phone_number = '+998' + phone_number.lstrip('0')

        user = User.objects.filter(phone_number=phone_number).first()

        if user:
            # Generate code
            code = str(random.randint(100000, 999999))
            PhoneVerification.objects.create(
                phone_number=phone_number,
                code=code,
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            # TODO: Send SMS
            messages.success(request, "SMS orqali kod yuborildi")
            return redirect('accounts:reset_password', token=code)
        else:
            messages.error(request, "Bu telefon raqam ro'yxatdan o'tmagan")

    return render(request, 'accounts/forgot_password.html')


def reset_password(request, token):
    """Parolni tiklash"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        code = request.POST.get('code')
        password = request.POST.get('password')

        if not phone_number.startswith('+998'):
            phone_number = '+998' + phone_number.lstrip('0')

        verification = PhoneVerification.objects.filter(
            phone_number=phone_number,
            code=code,
            is_used=False
        ).first()

        if verification and verification.is_valid:
            user = User.objects.filter(phone_number=phone_number).first()
            if user:
                user.set_password(password)
                user.save()
                verification.is_used = True
                verification.save()
                messages.success(request, "Parol muvaffaqiyatli o'zgartirildi")
                return redirect('accounts:login')
        else:
            messages.error(request, "Kod noto'g'ri yoki muddati o'tgan")

    return render(request, 'accounts/reset_password.html', {'token': token})


@login_required
def change_password(request):
    """Parolni o'zgartirish"""
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(current_password):
            messages.error(request, "Joriy parol noto'g'ri")
            return redirect('accounts:settings')

        if new_password != confirm_password:
            messages.error(request, "Yangi parollar mos kelmadi")
            return redirect('accounts:settings')

        request.user.set_password(new_password)
        request.user.save()
        update_session_auth_hash(request, request.user)

        messages.success(request, "Parol muvaffaqiyatli o'zgartirildi")

    return redirect('accounts:settings')


@login_required
def profile(request):
    """Profil sahifasi"""
    user = request.user

    # Statistika
    from tests_app.models import TestAttempt
    from competitions.models import Battle

    stats = {
        'tests': TestAttempt.objects.filter(user=user, status='completed').count(),
        'correct': user.total_correct_answers,
        'accuracy': user.accuracy_rate,
        'xp': user.xp_points,
        'level': user.get_level_display(),
        'streak': user.current_streak,
        'battles_won': Battle.objects.filter(winner=user).count(),
    }

    # Badgelar
    badges = UserBadge.objects.filter(user=user).select_related('badge')[:6]

    # So'nggi faoliyat
    activities = UserActivity.objects.filter(user=user)[:10]

    # Do'stlar
    friends_count = Friendship.objects.filter(
        Q(from_user=user) | Q(to_user=user),
        status='accepted'
    ).count()

    context = {
        'profile_user': user,
        'stats': stats,
        'badges': badges,
        'activities': activities,
        'friends_count': friends_count,
    }

    return render(request, 'accounts/profile.html', context)


def profile_public(request, uuid):
    """Ommaviy profil"""
    profile_user = get_object_or_404(User, uuid=uuid)

    # Statistika
    from tests_app.models import TestAttempt

    stats = {
        'tests': TestAttempt.objects.filter(user=profile_user, status='completed').count(),
        'accuracy': profile_user.accuracy_rate,
        'xp': profile_user.xp_points,
        'level': profile_user.get_level_display(),
        'rank': profile_user.global_rank,
    }

    # Badgelar
    badges = UserBadge.objects.filter(user=profile_user).select_related('badge')[:6]

    # Do'stlik holati
    is_friend = False
    friend_request_sent = False
    friend_request_received = False

    if request.user.is_authenticated and request.user != profile_user:
        friendship = Friendship.objects.filter(
            Q(from_user=request.user, to_user=profile_user) |
            Q(from_user=profile_user, to_user=request.user)
        ).first()

        if friendship:
            if friendship.status == 'accepted':
                is_friend = True
            elif friendship.from_user == request.user:
                friend_request_sent = True
            else:
                friend_request_received = True

    context = {
        'profile_user': profile_user,
        'stats': stats,
        'badges': badges,
        'is_friend': is_friend,
        'friend_request_sent': friend_request_sent,
        'friend_request_received': friend_request_received,
    }

    return render(request, 'accounts/profile_public.html', context)


@login_required
def profile_edit(request):
    """Profilni tahrirlash"""
    if request.method == 'POST':
        user = request.user

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.middle_name = request.POST.get('middle_name', '')
        user.email = request.POST.get('email', '')
        user.bio = request.POST.get('bio', '')
        user.birth_date = request.POST.get('birth_date') or None
        user.education_level = request.POST.get('education_level', user.education_level)
        user.school_name = request.POST.get('school_name', '')
        user.region = request.POST.get('region', '')
        user.district = request.POST.get('district', '')

        user.save()

        messages.success(request, "Profil yangilandi")
        return redirect('accounts:profile')

    return render(request, 'accounts/profile_edit.html')


@login_required
def profile_avatar(request):
    """Avatar yuklash"""
    if request.method == 'POST' and 'avatar' in request.FILES:
        request.user.avatar = request.FILES['avatar']
        request.user.save()
        messages.success(request, "Rasm yangilandi")

    return redirect('accounts:profile_edit')


@login_required
def settings(request):
    """Sozlamalar"""
    return render(request, 'accounts/settings.html')


@login_required
def notification_settings(request):
    """Bildirishnoma sozlamalari"""
    if request.method == 'POST':
        # Save notification preferences
        messages.success(request, "Sozlamalar saqlandi")

    return render(request, 'accounts/notification_settings.html')


@login_required
def privacy_settings(request):
    """Maxfiylik sozlamalari"""
    if request.method == 'POST':
        messages.success(request, "Sozlamalar saqlandi")

    return render(request, 'accounts/privacy_settings.html')


@login_required
def friends_list(request):
    """Do'stlar ro'yxati"""
    friendships = Friendship.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    ).select_related('from_user', 'to_user')

    friends = []
    for f in friendships:
        friend = f.to_user if f.from_user == request.user else f.from_user
        friends.append(friend)

    context = {
        'friends': friends,
    }

    return render(request, 'accounts/friends_list.html', context)


@login_required
def friend_requests(request):
    """Do'stlik so'rovlari"""
    received = Friendship.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user')

    sent = Friendship.objects.filter(
        from_user=request.user,
        status='pending'
    ).select_related('to_user')

    context = {
        'received': received,
        'sent': sent,
    }

    return render(request, 'accounts/friend_requests.html', context)


@login_required
def friend_add(request, user_id):
    """Do'st qo'shish"""
    to_user = get_object_or_404(User, id=user_id)

    if to_user == request.user:
        messages.error(request, "O'zingizga so'rov yubora olmaysiz")
        return redirect('accounts:friends_list')

    # Check existing
    existing = Friendship.objects.filter(
        Q(from_user=request.user, to_user=to_user) |
        Q(from_user=to_user, to_user=request.user)
    ).first()

    if existing:
        messages.warning(request, "So'rov allaqachon yuborilgan")
    else:
        Friendship.objects.create(
            from_user=request.user,
            to_user=to_user,
            status='pending'
        )
        messages.success(request, f"{to_user.first_name}ga do'stlik so'rovi yuborildi")

    return redirect('accounts:friends_list')


@login_required
def friend_accept(request, request_id):
    """Do'stlik so'rovini qabul qilish"""
    friendship = get_object_or_404(
        Friendship,
        id=request_id,
        to_user=request.user,
        status='pending'
    )

    friendship.status = 'accepted'
    friendship.save()

    # Log activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='friend_add',
        description=f"{friendship.from_user.first_name} bilan do'st bo'ldingiz"
    )

    messages.success(request, f"{friendship.from_user.first_name} bilan do'st bo'ldingiz!")
    return redirect('accounts:friend_requests')


@login_required
def friend_reject(request, request_id):
    """Do'stlik so'rovini rad etish"""
    friendship = get_object_or_404(
        Friendship,
        id=request_id,
        to_user=request.user,
        status='pending'
    )

    friendship.status = 'rejected'
    friendship.save()

    messages.info(request, "So'rov rad etildi")
    return redirect('accounts:friend_requests')


@login_required
def friend_remove(request, user_id):
    """Do'stlikni bekor qilish"""
    friend = get_object_or_404(User, id=user_id)

    Friendship.objects.filter(
        Q(from_user=request.user, to_user=friend) |
        Q(from_user=friend, to_user=request.user)
    ).delete()

    messages.info(request, f"{friend.first_name} do'stlar ro'yxatidan o'chirildi")
    return redirect('accounts:friends_list')


@login_required
def friend_search(request):
    """Do'st qidirish"""
    query = request.GET.get('q', '')
    users = []

    if query and len(query) >= 2:
        users = User.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone_number__icontains=query)
        ).exclude(id=request.user.id)[:20]

    context = {
        'query': query,
        'users': users,
    }

    return render(request, 'accounts/friend_search.html', context)


@login_required
def activity_log(request):
    """Faoliyat tarixi"""
    activities = UserActivity.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]

    context = {
        'activities': activities,
    }

    return render(request, 'accounts/activity_log.html', context)


@login_required
def badges(request):
    """Badgelar"""
    user_badges = UserBadge.objects.filter(
        user=request.user
    ).select_related('badge')

    all_badges = Badge.objects.filter(is_active=True)
    earned_ids = user_badges.values_list('badge_id', flat=True)

    context = {
        'user_badges': user_badges,
        'all_badges': all_badges,
        'earned_ids': list(earned_ids),
    }

    return render(request, 'accounts/badges.html', context)


# API Views

def api_check_phone(request):
    """Telefon raqam mavjudligini tekshirish"""
    phone = request.GET.get('phone', '')

    if not phone.startswith('+998'):
        phone = '+998' + phone.lstrip('0')

    exists = User.objects.filter(phone_number=phone).exists()

    return JsonResponse({'exists': exists})


@login_required
def api_profile_stats(request):
    """Profil statistikasi API"""
    user = request.user

    data = {
        'xp': user.xp_points,
        'level': user.level,
        'streak': user.current_streak,
        'tests': user.total_tests_taken,
        'accuracy': user.accuracy_rate,
        'rank': user.global_rank,
    }

    return JsonResponse(data)


"""
TestMakon.uz - Telegram Authentication
"""

import hashlib
import hmac
import time
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings

from accounts.models import User

# Telegram Bot Token
TELEGRAM_BOT_TOKEN = '8205738917:AAHIVL5FvDqOg-AM_6Qwe22_ey1JAcG_h78'
TELEGRAM_BOT_USERNAME = 'testmakonaibot'


def verify_telegram_auth(auth_data):
    """Telegram auth ma'lumotlarini tekshirish"""
    check_hash = auth_data.pop('hash', None)
    if not check_hash:
        return False

    # Auth date tekshirish (24 soat ichida bo'lishi kerak)
    auth_date = int(auth_data.get('auth_date', 0))
    if time.time() - auth_date > 86400:
        return False

    # Data-check-string yaratish
    data_check_arr = sorted([f'{key}={value}' for key, value in auth_data.items()])
    data_check_string = '\n'.join(data_check_arr)

    # Secret key
    secret_key = hashlib.sha256(TELEGRAM_BOT_TOKEN.encode()).digest()

    # Hash tekshirish
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    return calculated_hash == check_hash


def telegram_login(request):
    """Telegram login sahifasi"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    context = {
        'bot_username': TELEGRAM_BOT_USERNAME,
    }
    return render(request, 'accounts/telegram_login.html', context)


def telegram_callback(request):
    """Telegram callback handler"""
    # Auth ma'lumotlarini olish
    auth_data = {
        'id': request.GET.get('id'),
        'first_name': request.GET.get('first_name', ''),
        'last_name': request.GET.get('last_name', ''),
        'username': request.GET.get('username', ''),
        'photo_url': request.GET.get('photo_url', ''),
        'auth_date': request.GET.get('auth_date'),
        'hash': request.GET.get('hash'),
    }

    # Bo'sh qiymatlarni olib tashlash
    auth_data = {k: v for k, v in auth_data.items() if v}

    # Tekshirish
    hash_value = auth_data.get('hash')
    if not verify_telegram_auth(auth_data.copy()):
        messages.error(request, 'Telegram autentifikatsiya xatosi')
        return redirect('accounts:login')

    telegram_id = auth_data.get('id')
    first_name = auth_data.get('first_name', 'User')
    last_name = auth_data.get('last_name', '')
    username = auth_data.get('username', '')
    photo_url = auth_data.get('photo_url', '')

    # User ni topish yoki yaratish
    try:
        user = User.objects.get(telegram_id=telegram_id)
        # Ma'lumotlarni yangilash
        user.first_name = first_name
        user.last_name = last_name
        user.telegram_username = username
        user.telegram_photo_url = photo_url
        user.save()
    except User.DoesNotExist:
        # Yangi user yaratish
        # Telefon raqam sifatida telegram_id ishlatamiz (vaqtinchalik)
        phone_number = f'+998{str(telegram_id)[-9:]}'

        # Agar bunday telefon bor bo'lsa, unique qilish
        counter = 0
        original_phone = phone_number
        while User.objects.filter(phone_number=phone_number).exists():
            counter += 1
            phone_number = f'+998{str(telegram_id)[-9 - counter:-counter] if counter else str(telegram_id)[-9:]}'
            if counter > 5:
                phone_number = f'+998{telegram_id}'[-13:]
                break

        user = User.objects.create(
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name or 'User',
            telegram_id=telegram_id,
            telegram_username=username,
            telegram_photo_url=photo_url,
            is_phone_verified=True,  # Telegram orqali tasdiqlangan
        )

    # Login qilish
    login(request, user)
    user.update_streak()

    messages.success(request, f'Xush kelibsiz, {user.first_name}!')
    return redirect('core:dashboard')


def telegram_logout(request):
    """Logout"""
    logout(request)
    messages.info(request, 'Tizimdan chiqdingiz')
    return redirect('core:home')


# API endpoint for checking auth status
def api_telegram_check(request):
    """Telegram auth holatini tekshirish"""
    if request.user.is_authenticated:
        return JsonResponse({
            'authenticated': True,
            'user': {
                'id': request.user.id,
                'name': request.user.full_name,
                'telegram_id': request.user.telegram_id,
            }
        })
    return JsonResponse({'authenticated': False})