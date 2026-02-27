"""
TestMakon.uz - AI Core URLs
AI Mentor, Analysis, Study Plans
"""

from django.urls import path
from . import views

app_name = 'ai_core'

urlpatterns = [
    # AI Mentor Chat
    path('mentor/', views.ai_mentor, name='ai_mentor'),
    path('mentor/chat/', views.ai_chat, name='ai_chat'),
    path('mentor/conversation/<uuid:uuid>/', views.conversation_detail, name='conversation_detail'),
    path('mentor/conversations/', views.conversations_list, name='conversations_list'),
    path('mentor/conversation/<uuid:uuid>/delete/', views.conversation_delete, name='conversation_delete'),

    # AI Topic Tutor
    path('tutor/', views.ai_tutor, name='ai_tutor'),
    path('tutor/explain/', views.ai_explain_topic, name='ai_explain_topic'),

    # AI Test Analysis
    path('analyze/<uuid:attempt_uuid>/', views.ai_analyze_test, name='ai_analyze_test'),
    path('analyze/detailed/<uuid:attempt_uuid>/', views.ai_detailed_analysis, name='ai_detailed_analysis'),

    # AI University Advisor
    path('advisor/', views.ai_advisor, name='ai_advisor'),
    path('advisor/calculate/', views.ai_calculate_admission, name='ai_calculate_admission'),

    # Study Plans
    path('study-plan/', views.study_plan_list, name='study_plan_list'),
    path('study-plan/create/', views.study_plan_create, name='study_plan_create'),
    path('study-plan/<uuid:uuid>/', views.study_plan_detail, name='study_plan_detail'),
    path('study-plan/<uuid:uuid>/edit/', views.study_plan_edit, name='study_plan_edit'),
    path('study-plan/<uuid:uuid>/delete/', views.study_plan_delete, name='study_plan_delete'),
    path('study-plan/<uuid:uuid>/update/', views.study_plan_update, name='study_plan_update'),
    path('study-plan/<uuid:uuid>/regenerate/', views.regenerate_ai_plan, name='regenerate_ai_plan'),
    path('study-plan/task/<int:task_id>/complete/', views.task_complete, name='task_complete'),
    path('study-plan/task/<int:task_id>/start-test/', views.start_task_test, name='start_task_test'),

    # AI Recommendations
    path('recommendations/', views.recommendations_list, name='recommendations_list'),
    path('recommendations/dismiss/<int:id>/', views.recommendation_dismiss, name='recommendation_dismiss'),

    # Weak Topics
    path('weak-topics/', views.weak_topics, name='weak_topics'),

    # API
    path('api/chat/', views.api_chat, name='api_chat'),
    path('api/task/<str:task_id>/', views.api_task_status, name='api_task_status'),
    path('api/quick-answer/', views.api_quick_answer, name='api_quick_answer'),
    path('api/analyze/', views.api_analyze, name='api_analyze'),
]