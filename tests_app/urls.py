"""
TestMakon.uz - Tests App URLs
Subjects, tests, questions, results
"""

from django.urls import path
from . import views

app_name = 'tests_app'

urlpatterns = [
    # Subjects
    path('subjects/', views.subjects_list, name='subjects_list'),
    path('subjects/<slug:slug>/', views.subject_detail, name='subject_detail'),

    # Tests
    path('', views.tests_list, name='tests_list'),
    path('test/<slug:slug>/', views.test_detail, name='test_detail'),
    path('test/<slug:slug>/start/', views.test_start, name='test_start'),
    path('test/<uuid:uuid>/question/', views.test_question, name='test_question'),
    path('test/<uuid:uuid>/submit/', views.test_submit_answer, name='test_submit_answer'),
    path('test/<uuid:uuid>/finish/', views.test_finish, name='test_finish'),
    path('test/<uuid:uuid>/result/', views.test_result, name='test_result'),

    # Quick test (random questions)
    path('quick-test/', views.quick_test, name='quick_test'),
    path('quick-test/start/', views.quick_test_start, name='quick_test_start'),

    # Block test
    path('block-test/', views.block_test, name='block_test'),
    path('block-test/start/', views.block_test_start, name='block_test_start'),

    # Topic tests
    path('topic/<slug:subject_slug>/<slug:topic_slug>/', views.topic_test, name='topic_test'),

    # My results
    path('my-results/', views.my_results, name='my_results'),
    path('my-results/<uuid:uuid>/', views.result_detail, name='result_detail'),

    # Saved questions
    path('saved/', views.saved_questions, name='saved_questions'),
    path('save-question/<int:question_id>/', views.save_question, name='save_question'),
    path('unsave-question/<int:question_id>/', views.unsave_question, name='unsave_question'),

    # Wrong answers practice
    path('wrong-answers/', views.wrong_answers, name='wrong_answers'),
    path('wrong-answers/practice/', views.wrong_answers_practice, name='wrong_answers_practice'),

    # API
    path('api/subjects/', views.api_subjects, name='api_subjects'),
    path('api/test-progress/<uuid:uuid>/', views.api_test_progress, name='api_test_progress'),
]