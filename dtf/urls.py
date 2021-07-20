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

    path('projects/', views.ProjectListView.as_view(), name='projects'),
    path('projects/new', views.NewProjectView.as_view(), name='new_project'),

    path('users/sign_up', views.SignUpView.as_view(), name='sign_up'),
    path('users/sign_in', views.SignInView.as_view(), name='sign_in'),
    path('users/sign_out', views.SignOutView.as_view(), name='sign_out'),
    path('users/password/reset', views.ResetPasswordView.as_view(), name='reset_password'),
    path('users/password/reset_done', views.ResetPasswordDoneView.as_view(), name='reset_password_done'),
    path('users/password/confirm/<uidb64>/<token>/', views.ResetPasswordConfirmView.as_view(), name='reset_password_confirm'),
    path('users/password/reset_complete', views.ResetPasswordCompleteView.as_view(), name='reset_password_complete'),

    path('<str:project_slug>', RedirectView.as_view(pattern_name='project_submissions', permanent=False), name='project_details'),
    path('<str:project_slug>/members', views.ProjectMembersView.as_view(), name='project_members'),
    path('<str:project_slug>/settings', views.view_project_settings, name='project_settings'),
    path('<str:project_slug>/webhook/<int:webhook_id>/log', views.WebhookDetailView.as_view(), name='webhook_log'),
    path('<str:project_slug>/submissions', views.ProjectSubmissionListView.as_view(), name='project_submissions'),
    path('<str:project_slug>/submissions/<int:submission_id>', views.SubmissionDetailView.as_view(), name='submission_details'),
    path('<str:project_slug>/tests/<int:test_id>', views.TestResultDetailView.as_view(), name='test_result_details'),
    path('<str:project_slug>/tests/<int:test_id>/history', views.TestMeasurementHistoryView.as_view(), name='test_measurement_history'),
    path('<str:project_slug>/reference_sets', views.ProjectReferenceSetListView.as_view(), name='project_reference_sets'),
    path('<str:project_slug>/reference_sets/<int:reference_id>', views.ReferenceSetDetailView.as_view(), name='reference_set_details'),
    path('<str:project_slug>/test_references/<int:test_id>', views.TestReferenceDetailView.as_view(), name='test_reference_details'),

    path('api/users', api.UserList.as_view(), name='api_users'),
    path('api/users/<str:id>', api.UserDetail.as_view(), name='api_user'),

    path('api/projects', api.ProjectList.as_view(), name='api_projects'),
    path('api/projects/<str:id>', api.ProjectDetail.as_view(), name='api_project'),

    path('api/projects/<str:project_id>/members', api.ProjectMemberList.as_view(), name='api_project_members'),
    path('api/projects/<str:project_id>/members/<str:member_id>', api.ProjectMemberDetail.as_view(), name='api_project_member'),

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
    path('api/projects/<str:project_id>/submissions/<str:submission_id>/tests/<str:test_id>/history', api.TestMeasurementHistory.as_view(), name='api_project_submission_test_measurement_history'),

    path('api/projects/<str:project_id>/references', api.ProjectReferenceSetList.as_view(), name='api_project_references'),
    path('api/projects/<str:project_id>/references/<str:reference_id>', api.ProjectReferenceSetDetail.as_view(), name='api_project_reference'),

    path('api/projects/<str:project_id>/references/<str:reference_id>/tests', api.ProjectReferenceSetTestReferenceList.as_view(), name='api_project_reference_tests'),
    path('api/projects/<str:project_id>/references/<str:reference_id>/tests/<str:test_id>', api.ProjectReferenceSetTestReferenceDetail.as_view(), name='api_project_reference_test'),
]

urlpatterns = format_suffix_patterns(urlpatterns)
