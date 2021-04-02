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

    path('', RedirectView.as_view(pattern_name='projects', permanent=False)),
    path('projects/', views.view_projects, name='projects'),
    path('projects/new', views.view_new_project, name='new_project'),
    path('<str:project_slug>', views.view_project_details, name='project_details'),
    path('<str:project_slug>/settings', views.view_project_settings, name='project_settings'),
    path('<str:project_slug>/webhook/<int:webhook_id>/log', views.view_webhook_log, name='webhook_log'),
    path('<str:project_slug>/submissions/<int:submission_id>', views.view_submission_details, name='submission_details'),
    path('<str:project_slug>/tests/<int:test_id>', views.view_test_result_details, name='test_result_details'),

    path('api/projects', api.ProjectList.as_view(), name='api_projects'),
    path('api/projects/<str:id>', api.ProjectDetail.as_view(), name='api_project'),

    path('api/projects/<str:project_id>/properties', api.ProjectSubmissionPropertyList.as_view(), name='api_project_submission_properties'),
    path('api/projects/<str:project_id>/properties/<str:property_id>', api.ProjectSubmissionPropertyDetail.as_view(), name='api_project_submission_property'),

    path('api/projects/<str:project_id>/webhooks', api.ProjectWebhookList.as_view(), name='api_project_webhooks'),
    path('api/projects/<str:project_id>/webhooks/<str:webhook_id>', api.ProjectWebhookDetail.as_view(), name='api_project_webhook'),

    path('api/projects/<str:project_id>/webhooks/<str:webhook_id>/logs', api.ProjectWebhookLogList.as_view(), name='api_project_webhook_logs'),

    path('api/projects/<str:project_id>/submissions', api.ProjectSubmissionList.as_view(), name='api_project_submissions'),
    path('api/projects/<str:project_id>/submissions/<str:submission_id>', api.ProjectSubmissionDetail.as_view(), name='api_project_submission'),

    path('api/projects/<str:project_id>/submissions/<str:submission_id>/tests', api.ProjectSubmissionTestResultList.as_view(), name='api_project_submission_tests'),
    path('api/projects/<str:project_id>/submissions/<str:submission_id>/tests/<str:test_id>', api.ProjectSubmissionTestResultDetail.as_view(), name='api_project_submission_test'),

    path('api/projects/<str:project_id>/references', api.ProjectReferenceSetList.as_view(), name='api_project_references'),
    path('api/projects/<str:project_id>/references/<str:reference_id>', api.ProjectReferenceSetDetail.as_view(), name='api_project_reference'),

    path('api/projects/<str:project_id>/references/<str:reference_id>/tests', api.ProjectReferenceSetTestReferenceList.as_view(), name='api_project_reference_tests'),
    path('api/projects/<str:project_id>/references/<str:reference_id>/tests/<str:test_id>', api.ProjectReferenceSetTestReferenceDetail.as_view(), name='api_project_reference_test'),

    path('api/WIPE_DATABASE', api.WIPE_DATABASE),
]

urlpatterns = format_suffix_patterns(urlpatterns)
