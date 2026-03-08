from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api'

urlpatterns = [
    # ─── Auth ────────────────────────────────────────────
    path('auth/register/', views.RegisterView.as_view(), name='register'),
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/telegram-code/', views.TelegramCodeLoginView.as_view(), name='telegram_code_login'),
    path('auth/dev-code/', views.DevGenerateCodeView.as_view(), name='dev_generate_code'),

    # ─── Profile ─────────────────────────────────────────
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/avatar/', views.ProfileAvatarView.as_view(), name='profile_avatar'),

    # ─── Dashboard & Analytics ───────────────────────────
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),

    # ─── Subjects ────────────────────────────────────────
    path('subjects/', views.SubjectListView.as_view(), name='subject_list'),
    path('subjects/<slug:slug>/', views.SubjectDetailView.as_view(), name='subject_detail'),

    # ─── Tests ───────────────────────────────────────────
    path('tests/', views.TestListView.as_view(), name='test_list'),
    path('tests/<uuid:uuid>/', views.TestDetailView.as_view(), name='test_detail'),
    path('tests/<uuid:uuid>/start/', views.TestStartView.as_view(), name='test_start'),
    path('tests/attempt/<uuid:attempt_uuid>/finish/', views.TestFinishView.as_view(), name='test_finish'),

    # ─── Results ─────────────────────────────────────────
    path('results/', views.MyResultsView.as_view(), name='my_results'),
    path('results/<uuid:uuid>/', views.ResultDetailView.as_view(), name='result_detail'),

    # ─── AI Chat ─────────────────────────────────────────
    path('ai/conversations/', views.AIConversationListView.as_view(), name='ai_conversations'),
    path('ai/conversations/<int:pk>/', views.AIConversationDetailView.as_view(), name='ai_conversation_detail'),
    path('ai/chat/', views.AIChatView.as_view(), name='ai_chat'),
    path('ai/recommendations/', views.AIRecommendationListView.as_view(), name='ai_recommendations'),

    # ─── Saved Questions ─────────────────────────────────
    path('saved-questions/', views.SavedQuestionListView.as_view(), name='saved_questions'),
    path('saved-questions/<int:question_id>/toggle/', views.SavedQuestionToggleView.as_view(), name='saved_question_toggle'),

    # ─── Wrong Answers ───────────────────────────────────────────
    path("tests/wrong-answers/", views.WrongAnswersListView.as_view(), name="wrong_answers"),
    path("tests/wrong-answers/practice/", views.WrongAnswersPracticeView.as_view(), name="wrong_answers_practice"),

    # ─── Practice & Quick Test ───────────────────────────────────
    path("tests/practice/start/", views.PracticeStartView.as_view(), name="practice_start"),
    path("tests/quick-test/start/", views.QuickTestStartView.as_view(), name="quick_test_start"),

    # ─── Universities ────────────────────────────────────
    path('universities/', views.UniversityListView.as_view(), name='university_list'),
    path('universities/<slug:slug>/', views.UniversityDetailView.as_view(), name='university_detail'),

    # ─── News ────────────────────────────────────────────
    path('news/', views.ArticleListView.as_view(), name='news_list'),

    # ─── Leaderboard ─────────────────────────────────────
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
]