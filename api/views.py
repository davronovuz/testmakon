from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Q

from accounts.models import User, TelegramAuthCode, UserActivity
from tests_app.models import (
    Subject, Topic, Question, Answer, Test, TestAttempt,
    AttemptAnswer, SavedQuestion,
    UserTopicPerformance, UserSubjectPerformance, UserAnalyticsSummary,
)
from ai_core.models import AIConversation, AIMessage, AIRecommendation
from universities.models import University
from news.models import Article
from leaderboard.models import GlobalLeaderboard

from .serializers import (
    RegisterSerializer, LoginSerializer, UserProfileSerializer,
    SubjectSerializer, SubjectListSerializer,
    TestListSerializer, TestDetailSerializer,
    TestAttemptListSerializer, TestAttemptDetailSerializer,
    FinishTestSerializer,
    UserSubjectPerformanceSerializer, UserTopicPerformanceSerializer,
    UserAnalyticsSummarySerializer,
    AIConversationListSerializer, AIConversationSerializer,
    AIChatSerializer, AIMessageSerializer, AIRecommendationSerializer,
    UniversityListSerializer, UniversityDetailSerializer,
    ArticleListSerializer,
    SavedQuestionSerializer,
    LeaderboardSerializer,
)


# ─── AUTH ────────────────────────────────────────────────────

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user, context={'request': request}).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            phone_number=serializer.validated_data['phone_number'],
            password=serializer.validated_data['password'],
        )

        if not user:
            return Response(
                {'error': "Telefon raqam yoki parol noto'g'ri"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user, context={'request': request}).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


class TelegramCodeLoginView(APIView):
    """Telegram bot kodi orqali kirish/ro'yxatdan o'tish"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get('code', '').strip()

        if not code or len(code) != 6:
            return Response({'error': '6 xonali kodni kiriting'}, status=400)

        try:
            auth_code = TelegramAuthCode.objects.get(
                code=code,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
        except TelegramAuthCode.DoesNotExist:
            return Response(
                {'error': "Kod noto'g'ri yoki muddati o'tgan. Botdan yangi kod oling."},
                status=400,
            )

        auth_code.is_used = True
        auth_code.save()

        # User topish yoki yaratish
        try:
            user = User.objects.get(telegram_id=auth_code.telegram_id)
            if auth_code.telegram_username:
                user.telegram_username = auth_code.telegram_username
            if auth_code.telegram_first_name:
                user.first_name = auth_code.telegram_first_name
            user.save()
        except User.DoesNotExist:
            base_phone = f'+998{str(auth_code.telegram_id)[-9:].zfill(9)}'
            phone_number = base_phone
            counter = 0
            while User.objects.filter(phone_number=phone_number).exists():
                counter += 1
                phone_number = f'+998{str(auth_code.telegram_id + counter)[-9:].zfill(9)}'
                if counter > 10:
                    phone_number = f'+998{str(auth_code.telegram_id)[:9].zfill(9)}'
                    break

            user = User.objects.create(
                phone_number=phone_number,
                first_name=auth_code.telegram_first_name or 'User',
                telegram_id=auth_code.telegram_id,
                telegram_username=auth_code.telegram_username,
                is_phone_verified=True,
            )

        user.update_streak()
        UserActivity.objects.create(
            user=user,
            activity_type='login',
            description='Mobile app — Telegram bot orqali kirdi',
        )

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserProfileSerializer(user, context={'request': request}).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })


# ─── PROFILE ────────────────────────────────────────────────

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class ProfileAvatarView(APIView):
    def post(self, request):
        if 'avatar' not in request.FILES:
            return Response({'error': 'Avatar fayli kerak'}, status=400)

        request.user.avatar = request.FILES['avatar']
        request.user.save(update_fields=['avatar'])
        return Response({
            'avatar_url': request.build_absolute_uri(request.user.avatar.url)
        })


# ─── SUBJECTS ────────────────────────────────────────────────

class SubjectListView(generics.ListAPIView):
    serializer_class = SubjectListSerializer
    queryset = Subject.objects.filter(is_active=True)
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class SubjectDetailView(generics.RetrieveAPIView):
    serializer_class = SubjectSerializer
    queryset = Subject.objects.filter(is_active=True).prefetch_related('topics')
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


# ─── TESTS ───────────────────────────────────────────────────

class TestListView(generics.ListAPIView):
    serializer_class = TestListSerializer

    def get_queryset(self):
        qs = Test.objects.filter(is_active=True).select_related('subject')

        subject = self.request.query_params.get('subject')
        test_type = self.request.query_params.get('type')
        search = self.request.query_params.get('search')

        if subject:
            qs = qs.filter(subject__slug=subject)
        if test_type:
            qs = qs.filter(test_type=test_type)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return qs


class TestDetailView(generics.RetrieveAPIView):
    serializer_class = TestDetailSerializer
    queryset = Test.objects.filter(is_active=True)
    lookup_field = 'uuid'


# ─── TEST PLAY ───────────────────────────────────────────────

class TestStartView(APIView):
    def post(self, request, uuid):
        try:
            test = Test.objects.get(uuid=uuid, is_active=True)
        except Test.DoesNotExist:
            return Response({'error': 'Test topilmadi'}, status=404)

        if test.is_premium and not request.user.is_premium:
            return Response({'error': 'Bu test premium foydalanuvchilar uchun'}, status=403)

        questions = test.questions.filter(is_active=True)
        attempt = TestAttempt.objects.create(
            user=request.user,
            test=test,
            status='in_progress',
            total_questions=questions.count(),
        )

        return Response({
            'attempt_id': str(attempt.uuid),
            'test': TestDetailSerializer(test, context={'request': request}).data,
            'time_limit': test.time_limit,
        })


class TestFinishView(APIView):
    def post(self, request, attempt_uuid):
        try:
            attempt = TestAttempt.objects.get(
                uuid=attempt_uuid,
                user=request.user,
                status='in_progress',
            )
        except TestAttempt.DoesNotExist:
            return Response({'error': 'Attempt topilmadi'}, status=404)

        serializer = FinishTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        correct = 0
        wrong = 0
        skipped = 0

        for ans_data in serializer.validated_data['answers']:
            question_id = ans_data['question_id']
            answer_id = ans_data.get('answer_id')
            time_spent = ans_data.get('time_spent', 0)

            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                continue

            selected_answer = None
            is_correct = False

            if answer_id:
                try:
                    selected_answer = Answer.objects.get(id=answer_id, question=question)
                    is_correct = selected_answer.is_correct
                except Answer.DoesNotExist:
                    pass

            if answer_id is None:
                skipped += 1
            elif is_correct:
                correct += 1
            else:
                wrong += 1

            AttemptAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_answer': selected_answer,
                    'is_correct': is_correct,
                    'time_spent': time_spent,
                }
            )

            question.times_answered += 1
            if is_correct:
                question.times_correct += 1
            question.save(update_fields=['times_answered', 'times_correct'])

        attempt.correct_answers = correct
        attempt.wrong_answers = wrong
        attempt.skipped_questions = skipped
        attempt.status = 'completed'
        attempt.completed_at = timezone.now()
        attempt.time_spent = int((attempt.completed_at - attempt.started_at).total_seconds())
        attempt.calculate_results()

        user = request.user
        user.total_tests_taken += 1
        user.total_correct_answers += correct
        user.total_wrong_answers += wrong
        total = user.total_correct_answers + user.total_wrong_answers
        user.average_score = round((user.total_correct_answers / total) * 100, 1) if total else 0
        user.save(update_fields=[
            'total_tests_taken', 'total_correct_answers',
            'total_wrong_answers', 'average_score',
        ])
        user.add_xp(attempt.xp_earned)
        user.update_streak()

        try:
            from tests_app.tasks import process_user_stats_after_test
            process_user_stats_after_test.delay(attempt.id)
        except Exception:
            pass

        return Response(TestAttemptDetailSerializer(attempt).data)


# ─── RESULTS ─────────────────────────────────────────────────

class MyResultsView(generics.ListAPIView):
    serializer_class = TestAttemptListSerializer

    def get_queryset(self):
        qs = TestAttempt.objects.filter(
            user=self.request.user,
            status='completed',
        ).select_related('test')

        subject = self.request.query_params.get('subject')
        if subject:
            qs = qs.filter(test__subject__slug=subject)
        return qs


class ResultDetailView(generics.RetrieveAPIView):
    serializer_class = TestAttemptDetailSerializer
    lookup_field = 'uuid'

    def get_queryset(self):
        return TestAttempt.objects.filter(user=self.request.user)


# ─── DASHBOARD & ANALYTICS ──────────────────────────────────

class DashboardView(APIView):
    def get(self, request):
        user = request.user

        try:
            analytics = UserAnalyticsSummarySerializer(user.analytics_summary).data
        except UserAnalyticsSummary.DoesNotExist:
            analytics = None

        subject_perfs = UserSubjectPerformance.objects.filter(
            user=user
        ).select_related('subject')[:10]

        recent_results = TestAttempt.objects.filter(
            user=user, status='completed'
        ).select_related('test')[:5]

        recommendations = AIRecommendation.objects.filter(
            user=user, is_dismissed=False
        )[:5]

        return Response({
            'user': UserProfileSerializer(user, context={'request': request}).data,
            'analytics': analytics,
            'subject_performances': UserSubjectPerformanceSerializer(subject_perfs, many=True).data,
            'recent_results': TestAttemptListSerializer(recent_results, many=True).data,
            'recommendations': AIRecommendationSerializer(recommendations, many=True).data,
        })


class AnalyticsView(APIView):
    def get(self, request):
        user = request.user

        try:
            summary = UserAnalyticsSummarySerializer(user.analytics_summary).data
        except UserAnalyticsSummary.DoesNotExist:
            summary = None

        subject_perfs = UserSubjectPerformance.objects.filter(
            user=user
        ).select_related('subject')

        topic_perfs = UserTopicPerformance.objects.filter(
            user=user
        ).select_related('subject', 'topic')

        return Response({
            'summary': summary,
            'subject_performances': UserSubjectPerformanceSerializer(subject_perfs, many=True).data,
            'weak_topics': UserTopicPerformanceSerializer(topic_perfs.filter(is_weak=True), many=True).data,
            'strong_topics': UserTopicPerformanceSerializer(topic_perfs.filter(is_strong=True), many=True).data,
        })


# ─── AI CHAT ────────────────────────────────────────────────

class AIConversationListView(generics.ListCreateAPIView):
    serializer_class = AIConversationListSerializer

    def get_queryset(self):
        return AIConversation.objects.filter(user=self.request.user, is_active=True)

    def create(self, request, *args, **kwargs):
        conversation = AIConversation.objects.create(
            user=request.user,
            title='Yangi suhbat',
        )
        return Response(
            AIConversationSerializer(conversation).data,
            status=status.HTTP_201_CREATED,
        )


class AIConversationDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = AIConversationSerializer

    def get_queryset(self):
        return AIConversation.objects.filter(user=self.request.user)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=['is_active'])


class AIChatView(APIView):
    def post(self, request):
        serializer = AIChatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = serializer.validated_data['message']
        conv_id = serializer.validated_data.get('conversation_id')

        if conv_id:
            try:
                conversation = AIConversation.objects.get(id=conv_id, user=request.user)
            except AIConversation.DoesNotExist:
                return Response({'error': 'Suhbat topilmadi'}, status=404)
        else:
            conversation = AIConversation.objects.create(
                user=request.user,
                title=message[:50],
            )

        user_msg = AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=message,
        )

        try:
            from ai_core.tasks import ai_chat_task
            task = ai_chat_task.delay(conversation.id, message)
            result = task.get(timeout=30)
            ai_response = result.get('response', '') if isinstance(result, dict) else str(result)
        except Exception:
            ai_response = "Kechirasiz, texnik xatolik yuz berdi. Iltimos qayta urinib ko'ring."

        ai_msgs = AIMessage.objects.filter(
            conversation=conversation, role='assistant'
        ).order_by('-created_at')
        ai_msg = ai_msgs.first()

        if not ai_msg:
            ai_msg = AIMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=ai_response,
            )

        conversation.message_count = conversation.messages.count()
        conversation.save(update_fields=['message_count', 'updated_at'])

        return Response({
            'conversation_id': conversation.id,
            'user_message': AIMessageSerializer(user_msg).data,
            'ai_message': AIMessageSerializer(ai_msg).data,
        })


# ─── AI RECOMMENDATIONS ─────────────────────────────────────

class AIRecommendationListView(generics.ListAPIView):
    serializer_class = AIRecommendationSerializer

    def get_queryset(self):
        qs = AIRecommendation.objects.filter(user=self.request.user, is_dismissed=False)
        rec_type = self.request.query_params.get('type')
        if rec_type:
            qs = qs.filter(recommendation_type=rec_type)
        return qs


# ─── SAVED QUESTIONS ─────────────────────────────────────────

class SavedQuestionListView(generics.ListAPIView):
    serializer_class = SavedQuestionSerializer

    def get_queryset(self):
        return SavedQuestion.objects.filter(
            user=self.request.user
        ).select_related('question__subject', 'question__topic')


class SavedQuestionToggleView(APIView):
    def post(self, request, question_id):
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response({'error': 'Savol topilmadi'}, status=404)

        saved, created = SavedQuestion.objects.get_or_create(
            user=request.user, question=question,
        )
        if not created:
            saved.delete()
            return Response({'saved': False})
        return Response({'saved': True}, status=201)


# ─── UNIVERSITIES ────────────────────────────────────────────

class UniversityListView(generics.ListAPIView):
    serializer_class = UniversityListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = University.objects.filter(is_active=True)
        search = self.request.query_params.get('search')
        uni_type = self.request.query_params.get('type')
        region = self.request.query_params.get('region')

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(short_name__icontains=search))
        if uni_type:
            qs = qs.filter(university_type=uni_type)
        if region:
            qs = qs.filter(region__icontains=region)
        return qs


class UniversityDetailView(generics.RetrieveAPIView):
    serializer_class = UniversityDetailSerializer
    queryset = University.objects.filter(is_active=True)
    lookup_field = 'slug'
    permission_classes = [permissions.AllowAny]


# ─── NEWS ────────────────────────────────────────────────────

class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Article.objects.filter(is_published=True).order_by('-created_at')


# ─── LEADERBOARD ─────────────────────────────────────────────

class LeaderboardView(generics.ListAPIView):
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        period = self.request.query_params.get('period', 'weekly')
        return GlobalLeaderboard.objects.filter(
            period=period
        ).select_related('user').order_by('rank')[:100]