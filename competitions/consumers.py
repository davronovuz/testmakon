"""
WebSocket Consumer — Real-time bildirishnomalar
Do'stlik so'rovlari, battle invitelari, matchmaking natijasi
"""

import json
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
