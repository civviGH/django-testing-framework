"""
define the URLs for the project
"""

from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from dtf import views

urlpatterns = [
    path('', views.frontpage),
    path('projects/', views.view_projects, name='projects'),
    path('<str:project_slug>', views.view_project_details, name='project_details'),
    path('submission_details/<int:submission_id>', views.view_submission_details, name='submission_details'),
    path('test_details/<int:test_id>', views.view_test_result_details, name='test_result_details'),

    path('api/submit_test_results', views.submit_test_results),

    path('api/create_project', views.create_project),
    path('api/get_projects', views.get_projects, name='get_projects'),

    path('api/create_submission', views.create_submission, name='create_submission'),
    path('api/get_submission_by_id/<int:submission_id>',
     views.get_submission_by_id,
     name='get_submission_by_id'),

    path('api/get_reference/<str:project_name>/<str:test_name>',
     views.get_reference,
     name='get_reference'),
    path('api/get_reference_by_test_id/<int:test_id>',
     views.get_reference_by_test_id,
     name='get_reference_by_test_id'),
    path('api/update_references', views.update_references, name='update_references'),

    path('api/WIPE_DATABASE', views.WIPE_DATABASE),
]

urlpatterns = format_suffix_patterns(urlpatterns)
