"""
TestMakon.uz - Tests App URLs
Professional Question Bank + Test System
"""

from django.urls import path, re_path
from . import views

app_name = 'tests_app'

urlpatterns = [
    # ==========================================
    # QUESTION BANK (OnePrep kabi)
    # ==========================================
    path('', views.question_bank, name='question_bank'),
    path('bank/<slug:subject_slug>/', views.question_bank_subject, name='question_bank_subject'),

    # ==========================================
    # PRACTICE (Dinamik test)
    # ==========================================
    path('practice/', views.practice_select, name='practice_select'),
    path('practice/start/', views.practice_start, name='practice_start'),
    path('practice/<slug:subject_slug>/', views.practice_subject, name='practice_subject'),
    path('practice/<slug:subject_slug>/<slug:topic_slug>/', views.practice_topic, name='practice_topic'),

    # ==========================================
    # TEST PLAY (Professional UI)
    # ==========================================
    path('play/<uuid:uuid>/', views.test_play, name='test_play'),
    path('play/<uuid:uuid>/submit/', views.test_play_submit, name='test_play_submit'),
    path('play/<uuid:uuid>/finish/', views.test_play_finish, name='test_play_finish'),
    path('play/<uuid:uuid>/result/', views.test_play_result, name='test_play_result'),

    # ==========================================
    # SUBJECTS (Eski, redirect qiladi)
    # ==========================================
    path('subjects/', views.subjects_list, name='subjects_list'),
    path('subjects/<slug:slug>/', views.subject_detail, name='subject_detail'),

    # ==========================================
    # TESTS (Tayyor testlar)
    # ==========================================
    path('tests/', views.tests_list, name='tests_list'),
    path('test/<slug:slug>/', views.test_detail, name='test_detail'),
    path('test/<slug:slug>/start/', views.test_start, name='test_start'),

    # ==========================================
    # QUICK & BLOCK TEST
    # ==========================================
    path('quick-test/', views.quick_test, name='quick_test'),
    path('quick-test/start/', views.quick_test_start, name='quick_test_start'),
    path('block-test/', views.block_test, name='block_test'),
    path('block-test/start/', views.block_test_start, name='block_test_start'),

    # ==========================================
    # DTM SIMULATION
    # ==========================================
    path('dtm-simulation/', views.dtm_simulation, name='dtm_simulation'),
    path('dtm-simulation/start/', views.dtm_simulation_start, name='dtm_simulation_start'),

    # ==========================================
    # RESULTS
    # ==========================================
    path('my-results/', views.my_results, name='my_results'),
    path('my-results/<uuid:uuid>/', views.result_detail, name='result_detail'),

    # ==========================================
    # SAVED & WRONG ANSWERS
    # ==========================================
    path('saved/', views.saved_questions, name='saved_questions'),
    path('mistakes/', views.wrong_answers, name='wrong_answers'),
    path('mistakes/practice/', views.wrong_answers_practice, name='wrong_answers_practice'),

    # ==========================================
    # API ENDPOINTS
    # ==========================================
    path('api/subjects/', views.api_subjects, name='api_subjects'),
    path('api/topics/<int:subject_id>/', views.api_topics, name='api_topics'),
    path('api/questions/', views.api_questions, name='api_questions'),

    # Test play API
    path('api/play/<uuid:uuid>/status/', views.api_test_status, name='api_test_status'),
    path('api/play/<uuid:uuid>/navigate/', views.api_navigate, name='api_navigate'),
    path('api/play/<uuid:uuid>/bookmark/<int:question_id>/', views.api_bookmark, name='api_bookmark'),
    path('api/play/<uuid:uuid>/answer/', views.api_submit_answer, name='api_submit_answer'),
    path('api/play/<uuid:uuid>/time-sync/', views.api_time_sync, name='api_time_sync'),

    # Tools API
    path('api/tools/<slug:subject_slug>/', views.api_get_tools, name='api_get_tools'),

    # Save/Unsave
    path('api/save-question/<int:question_id>/', views.api_save_question, name='api_save_question'),

    # Anti-cheat
    path('api/log-violation/', views.api_log_violation, name='api_log_violation'),

    # ==========================================
    # STAFF: TEST VA SAVOL YARATISH UI
    # ==========================================
    path('manage/', views.manage_tests_list, name='manage_tests_list'),
    path('manage/create/', views.manage_test_create, name='manage_test_create'),
    re_path(r'^manage/(?P<slug>[\w.-]+)/edit/$', views.manage_test_edit, name='manage_test_edit'),
    re_path(r'^manage/(?P<slug>[\w.-]+)/delete/$', views.manage_test_delete, name='manage_test_delete'),
    re_path(r'^manage/(?P<slug>[\w.-]+)/questions/$', views.manage_test_questions, name='manage_test_questions'),
    re_path(r'^manage/(?P<slug>[\w.-]+)/questions/add/$', views.manage_question_create, name='manage_question_create'),
    re_path(r'^manage/(?P<slug>[\w.-]+)/questions/(?P<question_id>\d+)/edit/$', views.manage_question_edit, name='manage_question_edit'),
    re_path(r'^manage/(?P<slug>[\w.-]+)/questions/(?P<question_id>\d+)/link/$', views.manage_link_question, name='manage_link_question'),
    re_path(r'^manage/(?P<slug>[\w.-]+)/questions/(?P<question_id>\d+)/unlink/$', views.manage_unlink_question, name='manage_unlink_question'),

    # ==========================================
    # BULK IMPORT
    # ==========================================
    path('manage/import/', views.manage_bulk_import, name='manage_bulk_import'),
    path('manage/import/sample/', views.manage_download_sample_csv, name='manage_download_sample_csv'),

    # ==========================================
    # ESKI URL LAR (backward compatibility)
    # ==========================================
    path('test/<uuid:uuid>/question/', views.test_question, name='test_question'),
    path('test/<uuid:uuid>/submit/', views.test_submit_answer, name='test_submit_answer'),
    path('test/<uuid:uuid>/finish/', views.test_finish, name='test_finish'),
    path('test/<uuid:uuid>/result/', views.test_result, name='test_result'),
    path('topic/<slug:subject_slug>/<slug:topic_slug>/', views.topic_test, name='topic_test'),
    path('save-question/<int:question_id>/', views.save_question, name='save_question'),
    path('unsave-question/<int:question_id>/', views.unsave_question, name='unsave_question'),
    path('wrong-answers/', views.wrong_answers, name='wrong_answers_old'),
    path('wrong-answers/practice/', views.wrong_answers_practice, name='wrong_answers_practice_old'),
    path('api/test-progress/<uuid:uuid>/', views.api_test_progress, name='api_test_progress'),
]