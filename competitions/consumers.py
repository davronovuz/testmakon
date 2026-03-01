"""
WebSocket Consumer — Real-time bildirishnomalar
Do'stlik so'rovlari, battle invitelari, matchmaking natijasi
Olympiad va Mock Imtihon real-time boshqaruv
"""

import json
import asyncio
import datetime as dt
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    Foydalanuvchi shaxsiy notification kanali.
    Kanal nomi: user_{user_id}
    """

    async def connect(self):
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.user_id = user.id
        self.group_name = f'user_{self.user_id}'

        # Foydalanuvchi kanaliga qo'shilish
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # Online statusni do'stlarga bildirish
        await self.broadcast_online_status(True)

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            # Offline statusni do'stlarga bildirish
            await self.broadcast_online_status(False)

            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """Clientdan kelgan xabarlar (hozircha ping/pong)"""
        try:
            data = json.loads(text_data)
            msg_type = data.get('type', '')

            if msg_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
        except Exception:
            pass

    # ──────────────────────────────────────
    # XABAR HANDLERLAR (group_send orqali)
    # ──────────────────────────────────────

    async def friend_request(self, event):
        """Do'stlik so'rovi keldi"""
        await self.send(text_data=json.dumps({
            'type': 'friend_request_received',
            'from_user': event.get('from_user', {}),
            'friendship_id': event.get('friendship_id'),
        }))

    async def friend_accepted(self, event):
        """Do'stlik qabul qilindi"""
        await self.send(text_data=json.dumps({
            'type': 'friend_request_accepted',
            'from_user': event.get('from_user', {}),
        }))

    async def battle_invite(self, event):
        """Battle taklifi keldi"""
        await self.send(text_data=json.dumps({
            'type': 'battle_invite',
            'battle_uuid': event.get('battle_uuid'),
            'from_user': event.get('from_user', {}),
            'subject': event.get('subject', ''),
            'expires_in': event.get('expires_in', 60),
        }))

    async def match_found(self, event):
        """Matchmaking muvaffaqiyatli"""
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'battle_uuid': event.get('battle_uuid'),
            'opponent': event.get('opponent', {}),
        }))

    async def online_status(self, event):
        """Do'st online/offline bo'ldi"""
        await self.send(text_data=json.dumps({
            'type': 'online_status',
            'user_id': event.get('user_id'),
            'is_online': event.get('is_online'),
        }))

    async def push_notification(self, event):
        """Yangi bildirishnoma keldi (news.signals dan)"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event.get('notification', {}),
        }))

    # ──────────────────────────────────────
    # HELPER METHODLAR
    # ──────────────────────────────────────

    async def broadcast_online_status(self, is_online: bool):
        """Do'stlarga online status yuborish"""
        friend_ids = await self.get_friend_ids()

        for friend_id in friend_ids:
            await self.channel_layer.group_send(
                f'user_{friend_id}',
                {
                    'type': 'online.status',
                    'user_id': self.user_id,
                    'is_online': is_online,
                }
            )

    @database_sync_to_async
    def get_friend_ids(self):
        """Do'stlar ID lari (DB dan)"""
        try:
            from accounts.models import Friendship
            from django.db.models import Q

            friendships = Friendship.objects.filter(
                Q(from_user_id=self.user_id, status='accepted') |
                Q(to_user_id=self.user_id, status='accepted')
            ).values('from_user_id', 'to_user_id')

            ids = []
            for f in friendships:
                if f['from_user_id'] == self.user_id:
                    ids.append(f['to_user_id'])
                else:
                    ids.append(f['from_user_id'])
            return ids
        except Exception:
            return []


# ══════════════════════════════════════════════════════════════
# EXAM CONSUMER — Olimpiada / Mock Imtihon real-time boshqaruv
# ══════════════════════════════════════════════════════════════

class ExamConsumer(AsyncWebsocketConsumer):
    """
    Olimpiada va Mock Imtihon uchun real-time WebSocket.

    Kanallar:
      exam_{slug}         — barcha qatnashchilar
      exam_admin_{slug}   — faqat admin (control panel)

    Admin buyruqlari:
      {"type": "exam_control", "action": "start"}
      {"type": "exam_control", "action": "pause"}
      {"type": "exam_control", "action": "resume"}
      {"type": "exam_control", "action": "stop"}
      {"type": "exam_control", "action": "extend", "minutes": 10}
      {"type": "exam_control", "action": "announce", "message": "..."}

    Broadcast xabarlar (barcha qatnashchilarga):
      {"type": "exam_status", "status": "active", "seconds_remaining": 3600}
      {"type": "exam_paused"}
      {"type": "exam_resumed", "seconds_remaining": 3200}
      {"type": "exam_ended"}
      {"type": "timer_sync", "seconds_remaining": 3200}
      {"type": "leaderboard_update", "rankings": [...]}
      {"type": "participant_update", "count": 45, "joined": {...}}
      {"type": "announcement", "message": "..."}
    """

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.slug = self.scope['url_route']['kwargs']['slug']
        self.user = user
        self.is_admin = user.is_staff or user.is_superuser
        self.exam_group = f'exam_{self.slug}'
        self.admin_group = f'exam_admin_{self.slug}'
        self._timer_task = None

        # Imtihon mavjudligini tekshirish
        comp = await self.get_competition(self.slug)
        if not comp:
            await self.close(code=4004)
            return

        self.competition_id = comp['id']

        # Barcha qatnashchilar guruhiga qo'shish
        await self.channel_layer.group_add(self.exam_group, self.channel_name)

        # Admin ham o'z guruhiga qo'shiladi
        if self.is_admin:
            await self.channel_layer.group_add(self.admin_group, self.channel_name)

        await self.accept()

        # Joriy holat yuborish
        init_data = await self.build_init_data(comp)
        await self.send(text_data=json.dumps({'type': 'init', **init_data}))

        # Qatnashchilar sonini yangilash (admin ga)
        if not self.is_admin:
            count = await self.get_participant_count()
            await self.channel_layer.group_send(self.admin_group, {
                'type': 'admin.participant.update',
                'count': count,
                'user': {'id': user.id, 'name': user.full_name or user.phone_number},
            })

        # Timer sync task (admin uchun to'xtatiladi, qatnashchi uchun ishlaydi)
        if comp['status'] == 'active':
            self._timer_task = asyncio.ensure_future(self._timer_sync_loop(comp))

    async def disconnect(self, close_code):
        if hasattr(self, 'exam_group'):
            await self.channel_layer.group_discard(self.exam_group, self.channel_name)
        if self.is_admin and hasattr(self, 'admin_group'):
            await self.channel_layer.group_discard(self.admin_group, self.channel_name)
        if self._timer_task:
            self._timer_task.cancel()

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            msg_type = data.get('type', '')

            if msg_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))

            elif msg_type == 'exam_control' and self.is_admin:
                await self.handle_admin_control(data)

            elif msg_type == 'request_leaderboard':
                rankings = await self.get_live_leaderboard()
                await self.send(text_data=json.dumps({
                    'type': 'leaderboard_update',
                    'rankings': rankings,
                }))

        except Exception as e:
            await self.send(text_data=json.dumps({'type': 'error', 'message': str(e)}))

    # ─────────────────────────────────────────
    # ADMIN CONTROL
    # ─────────────────────────────────────────

    async def handle_admin_control(self, data):
        action = data.get('action', '')

        if action == 'start':
            await self.handle_start()

        elif action == 'pause':
            await self.handle_pause()

        elif action == 'resume':
            await self.handle_resume()

        elif action == 'stop':
            await self.handle_stop()

        elif action == 'extend':
            minutes = int(data.get('minutes', 10))
            await self.handle_extend(minutes)

        elif action == 'announce':
            message = data.get('message', '')
            if message:
                await self.channel_layer.group_send(self.exam_group, {
                    'type': 'broadcast.announcement',
                    'message': message,
                })

        elif action == 'leaderboard':
            rankings = await self.get_live_leaderboard()
            await self.channel_layer.group_send(self.exam_group, {
                'type': 'broadcast.leaderboard',
                'rankings': rankings,
            })

    @database_sync_to_async
    def do_start_exam(self):
        from .models import Competition
        from django.utils import timezone
        comp = Competition.objects.get(slug=self.slug)
        if comp.status in ('upcoming', 'registration', 'draft'):
            comp.status = 'active'
            # Agar start_time o'tmishda bo'lsa, hozirdan boshlaymiz
            now = timezone.now()
            if comp.start_time < now:
                comp.start_time = now
            comp.end_time = comp.start_time + dt.timedelta(minutes=comp.duration_minutes)
            comp.save(update_fields=['status', 'start_time', 'end_time'])
            return {'status': 'active', 'end_time': comp.end_time.isoformat()}
        return None

    @database_sync_to_async
    def do_pause_exam(self):
        from .models import Competition
        comp = Competition.objects.get(slug=self.slug)
        if comp.status == 'active':
            comp.status = 'paused'
            comp.save(update_fields=['status'])

    @database_sync_to_async
    def do_resume_exam(self):
        from .models import Competition
        import datetime
        comp = Competition.objects.get(slug=self.slug)
        if comp.status == 'paused':
            comp.status = 'active'
            # Qolgan vaqtni saqlab davom ettirish
            now = timezone.now()
            remaining = max(0, (comp.end_time - now).total_seconds())
            comp.end_time = now + datetime.timedelta(seconds=remaining)
            comp.save(update_fields=['status', 'end_time'])
            return int(remaining)
        return 0

    @database_sync_to_async
    def do_stop_exam(self):
        from .models import Competition
        comp = Competition.objects.get(slug=self.slug)
        comp.status = 'finished'
        comp.end_time = timezone.now()
        comp.save(update_fields=['status', 'end_time'])

    @database_sync_to_async
    def do_extend_exam(self, minutes):
        from .models import Competition
        import datetime
        comp = Competition.objects.get(slug=self.slug)
        comp.end_time = comp.end_time + datetime.timedelta(minutes=minutes)
        comp.duration_minutes += minutes
        comp.save(update_fields=['end_time', 'duration_minutes'])
        now = timezone.now()
        return int((comp.end_time - now).total_seconds())

    # Wrappers that broadcast after DB update
    async def handle_start(self):
        result = await self.do_start_exam()
        if result:
            await self.channel_layer.group_send(self.exam_group, {
                'type': 'broadcast.status',
                'status': 'active',
                'end_time': result['end_time'],
            })
            # Admin uchun timer loop boshlash (connect vaqtida active emas edi)
            if not self._timer_task or self._timer_task.done():
                self._timer_task = asyncio.ensure_future(
                    self._timer_sync_loop({'end_time': result['end_time']})
                )

    async def handle_pause(self):
        await self.do_pause_exam()
        await self.channel_layer.group_send(self.exam_group, {
            'type': 'broadcast.paused',
        })

    async def handle_resume(self):
        remaining = await self.do_resume_exam()
        await self.channel_layer.group_send(self.exam_group, {
            'type': 'broadcast.resumed',
            'seconds_remaining': remaining,
        })

    async def handle_stop(self):
        await self.do_stop_exam()
        await self.channel_layer.group_send(self.exam_group, {
            'type': 'broadcast.ended',
        })

    async def handle_extend(self, minutes):
        remaining = await self.do_extend_exam(minutes)
        await self.channel_layer.group_send(self.exam_group, {
            'type': 'broadcast.extended',
            'minutes_added': minutes,
            'seconds_remaining': remaining,
        })

    # ─────────────────────────────────────────
    # TIMER SYNC LOOP (har 30 soniyada)
    # ─────────────────────────────────────────

    async def _timer_sync_loop(self, comp):
        """Har 30 soniyada barcha qatnashchilarga qolgan vaqtni yuborish"""
        try:
            import datetime
            end_time_str = comp.get('end_time')
            if not end_time_str:
                return
            from django.utils.dateparse import parse_datetime
            end_time = parse_datetime(end_time_str) if isinstance(end_time_str, str) else end_time_str

            while True:
                await asyncio.sleep(30)
                now = timezone.now()
                remaining = max(0, int((end_time - now).total_seconds()))
                if remaining <= 0:
                    break
                await self.channel_layer.group_send(self.exam_group, {
                    'type': 'broadcast.timer',
                    'seconds_remaining': remaining,
                })
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    # ─────────────────────────────────────────
    # GROUP MESSAGE HANDLERS
    # ─────────────────────────────────────────

    async def broadcast_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'exam_status',
            'status': event.get('status'),
            'end_time': event.get('end_time'),
        }))

    async def broadcast_paused(self, event):
        await self.send(text_data=json.dumps({'type': 'exam_paused'}))

    async def broadcast_resumed(self, event):
        await self.send(text_data=json.dumps({
            'type': 'exam_resumed',
            'seconds_remaining': event.get('seconds_remaining', 0),
        }))

    async def broadcast_ended(self, event):
        await self.send(text_data=json.dumps({'type': 'exam_ended'}))

    async def broadcast_extended(self, event):
        await self.send(text_data=json.dumps({
            'type': 'exam_extended',
            'minutes_added': event.get('minutes_added'),
            'seconds_remaining': event.get('seconds_remaining'),
        }))

    async def broadcast_timer(self, event):
        await self.send(text_data=json.dumps({
            'type': 'timer_sync',
            'seconds_remaining': event.get('seconds_remaining'),
        }))

    async def broadcast_leaderboard(self, event):
        await self.send(text_data=json.dumps({
            'type': 'leaderboard_update',
            'rankings': event.get('rankings', []),
        }))

    async def broadcast_announcement(self, event):
        await self.send(text_data=json.dumps({
            'type': 'announcement',
            'message': event.get('message', ''),
        }))

    async def admin_participant_update(self, event):
        if self.is_admin:
            await self.send(text_data=json.dumps({
                'type': 'participant_update',
                'count': event.get('count'),
                'user': event.get('user'),
            }))

    # ─────────────────────────────────────────
    # DB HELPERS
    # ─────────────────────────────────────────

    @database_sync_to_async
    def get_competition(self, slug):
        from .models import Competition
        try:
            c = Competition.objects.get(slug=slug)
            return {
                'id': c.id,
                'slug': c.slug,
                'title': c.title,
                'status': c.status,
                'duration_minutes': c.duration_minutes,
                'end_time': c.end_time.isoformat() if c.end_time else None,
                'start_time': c.start_time.isoformat() if c.start_time else None,
                'show_live_leaderboard': c.show_live_leaderboard,
            }
        except Competition.DoesNotExist:
            return None

    @database_sync_to_async
    def build_init_data(self, comp):
        from .models import CompetitionParticipant
        now = timezone.now()
        end_time_str = comp.get('end_time')
        seconds_remaining = 0
        if end_time_str and comp['status'] == 'active':
            from django.utils.dateparse import parse_datetime
            end_time = parse_datetime(end_time_str) if isinstance(end_time_str, str) else end_time_str
            seconds_remaining = max(0, int((end_time - now).total_seconds()))

        count = CompetitionParticipant.objects.filter(competition_id=comp['id']).count()
        return {
            'status': comp['status'],
            'seconds_remaining': seconds_remaining,
            'participant_count': count,
            'is_admin': self.is_admin,
            'title': comp['title'],
        }

    @database_sync_to_async
    def get_participant_count(self):
        from .models import CompetitionParticipant
        return CompetitionParticipant.objects.filter(competition_id=self.competition_id).count()

    @database_sync_to_async
    def get_live_leaderboard(self):
        from .models import CompetitionParticipant
        participants = (
            CompetitionParticipant.objects
            .filter(competition_id=self.competition_id)
            .select_related('user')
            .order_by('-score', 'time_spent')[:20]
        )
        result = []
        for i, p in enumerate(participants, 1):
            result.append({
                'rank': i,
                'name': p.user.full_name or p.user.phone_number,
                'score': p.score,
                'correct': p.correct_answers,
                'time': p.time_spent,
                'status': p.status,
            })
        return result
