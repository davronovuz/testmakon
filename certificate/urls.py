from django.urls import path
from . import views

app_name = 'certificate'

urlpatterns = [
    # Fanlar ro'yxati
    path('', views.subjects_list, name='subjects_list'),

    # attempt/* URL lar — slug patternlardan OLDIN turishi shart!
    path('attempt/<uuid:attempt_uuid>/', views.mock_solve, name='mock_solve'),
    path('attempt/<uuid:attempt_uuid>/submit/', views.submit_answer, name='submit_answer'),
    path('attempt/<uuid:attempt_uuid>/finish/', views.mock_finish, name='mock_finish'),
    path('attempt/<uuid:attempt_uuid>/result/', views.mock_result, name='mock_result'),
    path('attempt/<uuid:attempt_uuid>/export/', views.export_result_json, name='export_result_json'),

    # Save/unsave question
    path('question/<int:question_id>/save/', views.toggle_save_question, name='toggle_save_question'),

    # Slug-based URL lar (oxirida)
    path('<slug:subject_slug>/', views.subject_mocks, name='subject_mocks'),
    path('<slug:subject_slug>/<slug:mock_slug>/', views.mock_detail, name='mock_detail'),
    path('<slug:subject_slug>/<slug:mock_slug>/start/', views.mock_start, name='mock_start'),
]
