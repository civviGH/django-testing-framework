from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

from rest_framework import permissions
from rest_framework import generics

from dtf.functions import get_object_or_none

def _is_sufficient_role(role, *, required_role):
    role_to_power = {
        'guest' : 1,
        'developer' : 2,
        'owner' : 3
    }
    required_power = role_to_power.get(required_role)
    if required_power is None:
        return False
    power = role_to_power.get(role)
    if power is None:
        return False
    return power >= required_power

def _get_requested_operation(request):
    if request.method in permissions.SAFE_METHODS:
        return 'view'
    if request.method == 'POST':
        return 'add'
    if request.method == 'PUT' or request.method == 'PATCH':
        return 'change'
    if request.method == 'DELETE':
        return 'delete'
    return None

def has_required_model_role(user, project, model, operation):
    if user.is_superuser:
        return True

    membership = get_object_or_none(project.memberships, user=user)
    if membership is None:
        return False

    required_role = model.required_project_membership_role.get(operation)

    return _is_sufficient_role(membership.role, required_role=required_role)

def check_required_model_role(user, project, model, operation):
    if not has_required_model_role(user, project, model, operation):
        raise PermissionDenied

class ProjectPermissionBase():

    def get_permission_project(self, request, **kwargs):
        return None

    def get_permission_models(self, request, **kwargs):
        return None

    def get_requested_operations(self, request, model, **kwargs):
        return [_get_requested_operation(request)]

    def has_permission(self, request, **kwargs):
        if not request.user.is_authenticated:
            return False

        project = self.get_permission_project(request, **kwargs)
        models = self.get_permission_models(request, **kwargs)
        if project is None or models is None:
            return False

        for model in models:
            requested_operations = self.get_requested_operations(request, model, **kwargs)
            for operation in requested_operations:
                if not has_required_model_role(request.user, project, model, operation):
                    return False

        return True

class ProjectPermission(ProjectPermissionBase, permissions.BasePermission):

    def get_permission_project(self, request, view):
        if hasattr(view, 'get_project'):
            return view.get_project()
        return None

    def get_permission_models(self, request, view):
        if isinstance(view, generics.GenericAPIView):
            return [view.serializer_class.Meta.model]
        elif hasattr(view, 'permission_model'):
            return [view.permission_model]
        return None

    def has_permission(self, request, view):
        return ProjectPermissionBase.has_permission(self, request, view=view)

class ProjectPermissionRequiredMixin(ProjectPermissionBase, AccessMixin):
    permission_models = None

    def get_permission_project(self, request):
        if hasattr(self, 'get_project'):
            return self.get_project()
        return None

    def get_permission_models(self, request):
        if self.permission_models is not None:
            return self.permission_models
        if hasattr(self, 'model'):
            return [self.model]
        return None

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(self.request):
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)
