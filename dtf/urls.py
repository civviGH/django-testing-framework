"""
define the URLs for the project
"""

from rest_framework.urlpatterns import format_suffix_patterns
from django.views.generic import RedirectView
from django.urls import path
from django.contrib import admin
from dtf import views
from dtf import api

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', RedirectView.as_view(pattern_name='projects', permanent=False), name="home"),

    path('projects/', views.view_projects, name='projects'),
    path('projects/new', views.view_new_project, name='new_project'),

    path('users/sign_up', views.view_sign_up, name='sign_up'),
    path('users/sign_in', views.SignInView.as_view(), name='sign_in'),
    path('users/sign_out', views.SignOutView.as_view(), name='sign_out'),
    path('users/password/reset', views.ResetPasswordView.as_view(), name='reset_password'),
    path('users/password/reset_done', views.ResetPasswordDoneView.as_view(), name='reset_password_done'),
    path('users/password/confirm/<uidb64>/<token>/', views.ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    path('users/password/reset_complete', views.ResetPasswordCompleteView.as_view(), name='reset_password_complete'),

    path('<str:project_slug>', RedirectView.as_view(pattern_name='project_submissions', permanent=False), name='project_details'),
    path('<str:project_slug>/settings', views.view_project_settings, name='project_settings'),
    path('<str:project_slug>/webhook/<int:webhook_id>/log', views.view_webhook_log, name='webhook_log'),
    path('<str:project_slug>/submissions', views.view_project_submissions, name='project_submissions'),
    path('<str:project_slug>/submissions/<int:submission_id>', views.view_submission_details, name='submission_details'),
    path('<str:project_slug>/tests/<int:test_id>', views.view_test_result_details, name='test_result_details'),
    path('<str:project_slug>/tests/<int:test_id>/history', views.view_test_measurement_history, name='test_measurement_history'),
    path('<str:project_slug>/reference_sets', views.view_project_reference_sets, name='project_reference_sets'),
    path('<str:project_slug>/reference_sets/<int:reference_id>', views.view_reference_set_details, name='reference_set_details'),
    path('<str:project_slug>/test_references/<int:test_id>', views.view_test_reference_details, name='test_reference_details'),

    path('api/projects', api.ProjectList.as_view(), name='api_projects'),
    path('api/projects/<str:id>', api.ProjectDetail.as_view(), name='api_project'),

    path('api/projects/<str:project_id>/properties', api.ProjectSubmissionPropertyList.as_view(), name='api_project_submission_properties'),
    path('api/projects/<str:project_id>/properties/<str:property_id>', api.ProjectSubmissionPropertyDetail.as_view(), name='api_project_submission_property'),

    path('api/projects/<str:project_id>/webhooks', api.ProjectWebhookList.as_view(), name='api_project_webhooks'),
    path('api/projects/<str:project_id>/webhooks/<str:webhook_id>', api.ProjectWebhookDetail.as_view(), name='api_project_webhook'),

    path('api/projects/<str:project_id>/webhooks/<str:webhook_id>/logs', api.ProjectWebhookLogList.as_view(), name='api_project_webhook_logs'),

    path('api/projects/<str:project_id>/tests', api.ProjectTestResultList.as_view(), name='api_project_tests'),
    path('api/projects/<str:project_id>/tests/<str:test_id>', api.ProjectTestResultDetail.as_view(), name='api_project_test'),

    path('api/projects/<str:project_id>/submissions', api.ProjectSubmissionList.as_view(), name='api_project_submissions'),
    path('api/projects/<str:project_id>/submissions/<str:submission_id>', api.ProjectSubmissionDetail.as_view(), name='api_project_submission'),

    path('api/projects/<str:project_id>/submissions/<str:submission_id>/tests', api.ProjectSubmissionTestResultList.as_view(), name='api_project_submission_tests'),
    path('api/projects/<str:project_id>/submissions/<str:submission_id>/tests/<str:test_id>', api.ProjectSubmissionTestResultDetail.as_view(), name='api_project_submission_test'),
    path('api/projects/<str:project_id>/submissions/<str:submission_id>/tests/<str:test_id>/history', api.get_test_measurement_history, name='api_project_submission_test_measurement_history'),

    path('api/projects/<str:project_id>/references', api.ProjectReferenceSetList.as_view(), name='api_project_references'),
    path('api/projects/<str:project_id>/references/<str:reference_id>', api.ProjectReferenceSetDetail.as_view(), name='api_project_reference'),

    path('api/projects/<str:project_id>/references/<str:reference_id>/tests', api.ProjectReferenceSetTestReferenceList.as_view(), name='api_project_reference_tests'),
    path('api/projects/<str:project_id>/references/<str:reference_id>/tests/<str:test_id>', api.ProjectReferenceSetTestReferenceDetail.as_view(), name='api_project_reference_test'),

    path('api/WIPE_DATABASE', api.WIPE_DATABASE),
]

urlpatterns = format_suffix_patterns(urlpatterns)
