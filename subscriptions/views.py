"""
TestMakon.uz - Subscriptions Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .models import (
    SubscriptionPlan, Subscription, Payment,
    PromoCode, PromoCodeUsage, UserDailyLimit
)


def pricing(request):
    """Narxlar sahifasi"""
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('order', 'price')

    # Foydalanuvchi joriy obunasi
    current_subscription = None
    if request.user.is_authenticated:
        current_subscription = Subscription.objects.filter(
            user=request.user,
            status='active'
        ).first()

    context = {
        'plans': plans,
        'current_subscription': current_subscription,
    }
    return render(request, 'subscriptions/pricing.html', context)


@login_required
def checkout(request, slug):
    """To'lov sahifasi"""
    plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)

    # Agar bepul bo'lsa
    if plan.price == 0:
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='pending'
        )
        subscription.activate()
        messages.success(request, f'{plan.name} paketi faollashtirildi!')
        return redirect('core:dashboard')

    # Promo kod
    promo_code = None
    discount = 0
    final_price = plan.price

    if request.method == 'POST':
        promo_code_text = request.POST.get('promo_code', '').strip().upper()
        if promo_code_text:
            try:
                promo = PromoCode.objects.get(code=promo_code_text)
                if promo.is_valid:
                    # User ishlatgan mi
                    used_count = PromoCodeUsage.objects.filter(
                        promo_code=promo,
                        user=request.user
                    ).count()
                    if used_count < promo.max_uses_per_user:
                        promo_code = promo
                        final_price = promo.apply_discount(plan.price)
                        discount = plan.price - final_price
                        messages.success(request, f'Promo kod qo\'llandi! {discount:,} so\'m chegirma')
                    else:
                        messages.error(request, 'Siz bu promo kodni allaqachon ishlatgansiz')
                else:
                    messages.error(request, 'Promo kod muddati tugagan')
            except PromoCode.DoesNotExist:
                messages.error(request, 'Noto\'g\'ri promo kod')

    context = {
        'plan': plan,
        'promo_code': promo_code,
        'discount': discount,
        'final_price': final_price,
    }
    return render(request, 'subscriptions/checkout.html', context)


@login_required
def process_payment(request, slug):
    """To'lovni qayta ishlash"""
    if request.method != 'POST':
        return redirect('subscriptions:checkout', slug=slug)

    plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)
    provider = request.POST.get('provider', 'click')
    promo_code_text = request.POST.get('promo_code', '').strip().upper()

    # Narxni hisoblash
    final_price = plan.price
    promo = None

    if promo_code_text:
        try:
            promo = PromoCode.objects.get(code=promo_code_text)
            if promo.is_valid:
                final_price = promo.apply_discount(plan.price)
        except PromoCode.DoesNotExist:
            pass

    # Subscription yaratish
    subscription = Subscription.objects.create(
        user=request.user,
        plan=plan,
        status='pending'
    )

    # Payment yaratish
    payment = Payment.objects.create(
        user=request.user,
        subscription=subscription,
        plan=plan,
        amount=final_price,
        provider=provider,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )

    # Promo kod ishlatilgan bo'lsa
    if promo:
        PromoCodeUsage.objects.create(
            promo_code=promo,
            user=request.user,
            payment=payment,
            discount_amount=plan.price - final_price
        )
        promo.use()

    # Demo uchun - to'lovni avtomatik tasdiqlash
    # Real loyihada Click/Payme API ga yo'naltirish kerak
    if provider == 'demo':
        payment.mark_as_paid()
        messages.success(request, f'{plan.name} paketi muvaffaqiyatli faollashtirildi!')
        return redirect('subscriptions:success', uuid=payment.uuid)

    # Click/Payme sahifasiga yo'naltirish
    context = {
        'payment': payment,
        'plan': plan,
    }
    return render(request, 'subscriptions/payment_redirect.html', context)


@login_required
def payment_success(request, uuid):
    """To'lov muvaffaqiyatli"""
    payment = get_object_or_404(Payment, uuid=uuid, user=request.user)

    context = {
        'payment': payment,
    }
    return render(request, 'subscriptions/success.html', context)


@login_required
def payment_failed(request, uuid):
    """To'lov muvaffaqiyatsiz"""
    payment = get_object_or_404(Payment, uuid=uuid, user=request.user)

    context = {
        'payment': payment,
    }
    return render(request, 'subscriptions/failed.html', context)


@login_required
def my_subscription(request):
    """Mening obunalarim"""
    subscriptions = Subscription.objects.filter(user=request.user).order_by('-created_at')
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:10]

    current = subscriptions.filter(status='active').first()

    context = {
        'subscriptions': subscriptions,
        'payments': payments,
        'current': current,
    }
    return render(request, 'subscriptions/my_subscription.html', context)


@login_required
def cancel_subscription(request):
    """Obunani bekor qilish"""
    if request.method != 'POST':
        return redirect('subscriptions:my_subscription')

    subscription = Subscription.objects.filter(
        user=request.user,
        status='active'
    ).first()

    if subscription:
        subscription.cancel()
        messages.info(request, 'Obuna bekor qilindi. Premium muddat tugagunicha amal qiladi.')

    return redirect('subscriptions:my_subscription')


# API Views

@login_required
def api_check_promo(request):
    """Promo kodni tekshirish API"""
    code = request.GET.get('code', '').strip().upper()
    plan_slug = request.GET.get('plan', '')

    if not code:
        return JsonResponse({'valid': False, 'error': 'Kod kiritilmagan'})

    try:
        promo = PromoCode.objects.get(code=code)

        if not promo.is_valid:
            return JsonResponse({'valid': False, 'error': 'Promo kod muddati tugagan'})

        # User ishlatgan mi
        used_count = PromoCodeUsage.objects.filter(
            promo_code=promo,
            user=request.user
        ).count()

        if used_count >= promo.max_uses_per_user:
            return JsonResponse({'valid': False, 'error': 'Siz bu kodni allaqachon ishlatgansiz'})

        # Discount hisoblash
        try:
            plan = SubscriptionPlan.objects.get(slug=plan_slug)
            original_price = plan.price
            final_price = promo.apply_discount(original_price)
            discount = original_price - final_price

            return JsonResponse({
                'valid': True,
                'discount': discount,
                'final_price': final_price,
                'discount_text': f'{promo.discount_value}{"%" if promo.discount_type == "percent" else " som"}'
            })
        except SubscriptionPlan.DoesNotExist:
            return JsonResponse({'valid': True, 'discount': 0})

    except PromoCode.DoesNotExist:
        return JsonResponse({'valid': False, 'error': 'Noto\'g\'ri promo kod'})


@login_required
def api_check_limits(request):
    """Kunlik limitlarni tekshirish"""
    user = request.user

    # Joriy obuna
    subscription = Subscription.objects.filter(
        user=user,
        status='active'
    ).first()

    if subscription:
        plan = subscription.plan
    else:
        # Bepul paket
        plan = SubscriptionPlan.objects.filter(plan_type='free', is_active=True).first()
        if not plan:
            return JsonResponse({
                'can_take_test': True,
                'can_use_ai': True,
                'is_premium': False
            })

    # Kunlik limit
    daily = UserDailyLimit.get_or_create_today(user)

    return JsonResponse({
        'can_take_test': daily.can_take_test(plan),
        'can_use_ai': daily.can_use_ai_chat(plan),
        'tests_remaining': (plan.daily_test_limit - daily.tests_taken) if plan.daily_test_limit else None,
        'ai_remaining': (plan.daily_ai_chat_limit - daily.ai_chats_used) if plan.daily_ai_chat_limit else None,
        'is_premium': user.is_premium,
        'plan_name': plan.name
    })


@login_required
def manual_payment(request, slug):
    """Qo'lda to'lov — chek yuborish sahifasi"""
    plan = get_object_or_404(SubscriptionPlan, slug=slug, is_active=True)

    # Promo kod session dan olish
    promo_code_text = request.GET.get('promo_code', '').strip().upper()
    final_price = plan.price
    discount = 0
    promo = None

    if promo_code_text:
        try:
            promo = PromoCode.objects.get(code=promo_code_text)
            if promo.is_valid:
                final_price = promo.apply_discount(plan.price)
                discount = plan.price - final_price
        except PromoCode.DoesNotExist:
            pass

    if request.method == 'POST':
        receipt = request.FILES.get('receipt_image')
        sender_name = request.POST.get('sender_name', '').strip()

        if not receipt:
            messages.error(request, 'Chek rasmini yuklang!')
            return redirect('subscriptions:manual_payment', slug=slug)

        # Subscription yaratish (pending)
        subscription = Subscription.objects.create(
            user=request.user,
            plan=plan,
            status='pending'
        )

        # Payment yaratish
        payment = Payment.objects.create(
            user=request.user,
            subscription=subscription,
            plan=plan,
            amount=final_price,
            provider='manual',
            status='pending',
            receipt_image=receipt,
            description=f"Jo'natuvchi: {sender_name}" if sender_name else '',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )

        # Promo kod bo'lsa
        if promo:
            PromoCodeUsage.objects.create(
                promo_code=promo,
                user=request.user,
                payment=payment,
                discount_amount=discount
            )
            promo.use()

        messages.success(request, 'Chekingiz qabul qilindi! Admin tasdiqlashidan so\'ng premium faollashadi.')
        return redirect('subscriptions:manual_pending', uuid=payment.uuid)

    context = {
        'plan': plan,
        'final_price': final_price,
        'discount': discount,
        'promo_code_text': promo_code_text,
    }
    return render(request, 'subscriptions/manual_payment.html', context)


@login_required
def manual_pending(request, uuid):
    """Qo'lda to'lov — kutish sahifasi"""
    payment = get_object_or_404(Payment, uuid=uuid, user=request.user)
    context = {'payment': payment}
    return render(request, 'subscriptions/manual_pending.html', context)


# Click/Payme Webhook handlers (demo)

@csrf_exempt
def click_webhook(request):
    """Click webhook handler"""
    # Real loyihada Click API dokumentatsiyasiga qarang
    # Bu yerda faqat demo
    return JsonResponse({'status': 'ok'})


@csrf_exempt
def payme_webhook(request):
    """Payme webhook handler"""
    # Real loyihada Payme API dokumentatsiyasiga qarang
    # Bu yerda faqat demo
    return JsonResponse({'status': 'ok'})


# Helper functions

def get_client_ip(request):
    """Client IP olish"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip