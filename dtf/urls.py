"""
define the URLs for the project
"""

from rest_framework.urlpatterns import format_suffix_patterns
from django.urls import path
from django.contrib import admin
from dtf import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', views.frontpage),
    path('projects/', views.view_projects, name='projects'),
    path('projects/new', views.view_new_project, name='new_project'),
    path('<str:project_slug>', views.view_project_details, name='project_details'),
    path('<str:project_slug>/settings', views.view_project_settings, name='project_settings'),
    path('submission_details/<int:submission_id>', views.view_submission_details, name='submission_details'),
    path('test_details/<int:test_id>', views.view_test_result_details, name='test_result_details'),

    path('api/submit_test_results', views.submit_test_results),

    path('api/projects', views.projects, name='api_projects'),
    path('api/projects/<str:id>', views.project, name='api_project'),

    path('api/projects/<str:project_id>/properties', views.project_submission_properties, name='api_project_submission_properties'),
    path('api/projects/<str:project_id>/properties/<str:property_id>', views.project_submission_property, name='api_project_submission_property'),

    path('api/create_submission', views.create_submission, name='create_submission'),
    path('api/get_submission_by_id/<int:submission_id>',
     views.get_submission_by_id,
     name='get_submission_by_id'),

    path('api/get_reference/<str:project_slug>/<str:test_name>',
     views.get_reference,
     name='get_reference'),
    path('api/get_reference_by_test_id/<int:test_id>',
     views.get_reference_by_test_id,
     name='get_reference_by_test_id'),
    path('api/update_references', views.update_references, name='update_references'),

    path('api/WIPE_DATABASE', views.WIPE_DATABASE),
]

urlpatterns = format_suffix_patterns(urlpatterns)
