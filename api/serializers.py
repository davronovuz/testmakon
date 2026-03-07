from rest_framework import serializers
from accounts.models import User
from tests_app.models import (
    Subject, Topic, Question, Answer, Test, TestQuestion,
    TestAttempt, AttemptAnswer, SavedQuestion,
    UserTopicPerformance, UserSubjectPerformance, UserAnalyticsSummary,
)
from ai_core.models import AIConversation, AIMessage, AIRecommendation
from universities.models import University, Direction, PassingScore
from news.models import Article
from leaderboard.models import GlobalLeaderboard


# ─── AUTH ────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['phone_number', 'password', 'first_name', 'last_name']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'uuid', 'phone_number', 'first_name', 'last_name',
            'middle_name', 'email', 'avatar_url', 'bio', 'birth_date',
            'education_level', 'school_name', 'region', 'district',
            'xp_points', 'level', 'current_streak', 'longest_streak',
            'total_tests_taken', 'total_correct_answers', 'total_wrong_answers',
            'average_score', 'accuracy_rate', 'rating',
            'global_rank', 'weekly_rank', 'is_premium', 'premium_until',
            'created_at',
        ]
        read_only_fields = [
            'id', 'uuid', 'phone_number', 'xp_points', 'level',
            'current_streak', 'longest_streak', 'total_tests_taken',
            'total_correct_answers', 'total_wrong_answers', 'average_score',
            'rating', 'global_rank', 'weekly_rank', 'is_premium',
            'premium_until', 'created_at',
        ]

    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


# ─── SUBJECTS & TOPICS ──────────────────────────────────────

class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'name', 'slug', 'description', 'order']


class SubjectSerializer(serializers.ModelSerializer):
    topics = TopicSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'color',
            'image_url', 'total_tests', 'total_questions', 'topics',
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


class SubjectListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Subject
        fields = ['id', 'name', 'slug', 'icon', 'color', 'image_url', 'total_tests', 'total_questions']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None


# ─── QUESTIONS & ANSWERS ─────────────────────────────────────

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'order']


class AnswerWithCorrectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct', 'order']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True, default=None)

    class Meta:
        model = Question
        fields = [
            'id', 'uuid', 'text', 'question_type', 'difficulty',
            'points', 'time_limit', 'subject_name', 'topic_name', 'answers',
        ]


class QuestionWithExplanationSerializer(serializers.ModelSerializer):
    answers = AnswerWithCorrectSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = [
            'id', 'uuid', 'text', 'question_type', 'difficulty',
            'points', 'explanation', 'hint', 'answers',
        ]


# ─── TESTS ───────────────────────────────────────────────────

class TestListSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default=None)

    class Meta:
        model = Test
        fields = [
            'id', 'uuid', 'title', 'slug', 'description', 'test_type',
            'subject_name', 'time_limit', 'question_count', 'passing_score',
            'is_premium', 'total_attempts', 'average_score',
        ]


class TestDetailSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True, default=None)
    questions = serializers.SerializerMethodField()

    class Meta:
        model = Test
        fields = [
            'id', 'uuid', 'title', 'description', 'test_type',
            'subject_name', 'time_limit', 'question_count', 'passing_score',
            'shuffle_questions', 'shuffle_answers', 'show_correct_answers',
            'questions',
        ]

    def get_questions(self, obj):
        qs = obj.questions.filter(is_active=True).prefetch_related('answers')
        if obj.shuffle_questions:
            qs = qs.order_by('?')
        return QuestionSerializer(qs, many=True).data


# ─── TEST ATTEMPT ────────────────────────────────────────────

class TestAttemptListSerializer(serializers.ModelSerializer):
    test_title = serializers.CharField(source='test.title', read_only=True)
    test_type = serializers.CharField(source='test.test_type', read_only=True)

    class Meta:
        model = TestAttempt
        fields = [
            'id', 'uuid', 'test_title', 'test_type', 'status',
            'total_questions', 'correct_answers', 'wrong_answers',
            'percentage', 'score', 'xp_earned', 'time_spent',
            'started_at', 'completed_at',
        ]


class TestAttemptDetailSerializer(serializers.ModelSerializer):
    test_title = serializers.CharField(source='test.title', read_only=True)
    answers = serializers.SerializerMethodField()
    weak_topics = serializers.JSONField(read_only=True)
    strong_topics = serializers.JSONField(read_only=True)

    class Meta:
        model = TestAttempt
        fields = [
            'id', 'uuid', 'test_title', 'status',
            'total_questions', 'correct_answers', 'wrong_answers',
            'skipped_questions', 'percentage', 'score', 'xp_earned',
            'time_spent', 'started_at', 'completed_at',
            'ai_analysis', 'weak_topics', 'strong_topics', 'answers',
        ]

    def get_answers(self, obj):
        attempt_answers = obj.answers.select_related(
            'question', 'selected_answer'
        ).all()
        return AttemptAnswerSerializer(attempt_answers, many=True).data


class AttemptAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    selected_answer_text = serializers.SerializerMethodField()
    correct_answer_text = serializers.SerializerMethodField()
    explanation = serializers.CharField(source='question.explanation', read_only=True)

    class Meta:
        model = AttemptAnswer
        fields = [
            'id', 'question_text', 'selected_answer_text',
            'correct_answer_text', 'is_correct', 'time_spent', 'explanation',
        ]

    def get_selected_answer_text(self, obj):
        if obj.selected_answer:
            return obj.selected_answer.text
        return None

    def get_correct_answer_text(self, obj):
        correct = obj.question.answers.filter(is_correct=True).first()
        return correct.text if correct else None


class SubmitAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer_id = serializers.IntegerField(required=False, allow_null=True)
    time_spent = serializers.IntegerField(default=0)


class FinishTestSerializer(serializers.Serializer):
    answers = SubmitAnswerSerializer(many=True)


# ─── ANALYTICS ───────────────────────────────────────────────

class UserTopicPerformanceSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    topic_name = serializers.CharField(source='topic.name', read_only=True)

    class Meta:
        model = UserTopicPerformance
        fields = [
            'id', 'subject_name', 'topic_name',
            'total_questions', 'correct_answers', 'wrong_answers',
            'current_score', 'best_score', 'score_trend',
            'is_weak', 'is_strong', 'is_mastered', 'last_practiced',
        ]


class UserSubjectPerformanceSerializer(serializers.ModelSerializer):
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_icon = serializers.CharField(source='subject.icon', read_only=True)
    subject_color = serializers.CharField(source='subject.color', read_only=True)

    class Meta:
        model = UserSubjectPerformance
        fields = [
            'id', 'subject_name', 'subject_icon', 'subject_color',
            'total_tests', 'total_questions', 'correct_answers',
            'average_score', 'best_score', 'last_score',
            'predicted_dtm_score', 'last_practiced',
        ]


class UserAnalyticsSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnalyticsSummary
        fields = [
            'total_study_time', 'total_questions_solved', 'total_tests_completed',
            'overall_accuracy', 'avg_questions_per_day',
            'weak_topics_count', 'strong_topics_count', 'mastered_topics_count',
            'predicted_dtm_score', 'university_match_count',
            'current_streak', 'longest_streak', 'learning_style',
            'best_study_hours', 'best_study_days',
        ]


# ─── AI ──────────────────────────────────────────────────────

class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = ['id', 'role', 'content', 'created_at']


class AIConversationSerializer(serializers.ModelSerializer):
    messages = AIMessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = AIConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages', 'last_message']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {'content': msg.content[:100], 'role': msg.role, 'created_at': msg.created_at}
        return None


class AIConversationListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AIConversation
        fields = ['id', 'title', 'created_at', 'updated_at', 'last_message', 'message_count']

    def get_last_message(self, obj):
        msg = obj.messages.order_by('-created_at').first()
        if msg:
            return {'content': msg.content[:100], 'role': msg.role}
        return None

    def get_message_count(self, obj):
        return obj.messages.count()


class AIChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)


class AIRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIRecommendation
        fields = ['id', 'recommendation_type', 'title', 'content', 'priority', 'created_at']


# ─── UNIVERSITIES ────────────────────────────────────────────

class PassingScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = PassingScore
        fields = ['year', 'grant_score', 'contract_score']


class DirectionSerializer(serializers.ModelSerializer):
    passing_scores = PassingScoreSerializer(many=True, read_only=True)

    class Meta:
        model = Direction
        fields = ['id', 'name', 'code', 'passing_scores']


class UniversityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'slug', 'city', 'university_type']


class UniversityDetailSerializer(serializers.ModelSerializer):
    directions = DirectionSerializer(many=True, read_only=True)

    class Meta:
        model = University
        fields = ['id', 'name', 'slug', 'description', 'city', 'university_type', 'directions']


# ─── NEWS ────────────────────────────────────────────────────

class ArticleListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = ['id', 'title', 'slug', 'excerpt', 'image_url', 'views_count', 'created_at']

    def get_image_url(self, obj):
        if obj.featured_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.featured_image.url)
        return None


# ─── SAVED QUESTIONS ─────────────────────────────────────────

class SavedQuestionSerializer(serializers.ModelSerializer):
    question = QuestionWithExplanationSerializer(read_only=True)

    class Meta:
        model = SavedQuestion
        fields = ['id', 'question', 'note', 'created_at']


# ─── LEADERBOARD ─────────────────────────────────────────────

class LeaderboardSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_avatar = serializers.SerializerMethodField()
    user_level = serializers.CharField(source='user.level', read_only=True)

    class Meta:
        model = GlobalLeaderboard
        fields = ['rank', 'user_name', 'user_avatar', 'user_level', 'xp_earned', 'tests_completed', 'accuracy_rate']

    def get_user_avatar(self, obj):
        if obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
        return None