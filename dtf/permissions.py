from django.core.exceptions import PermissionDenied

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

class ProjectPermission(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if isinstance(view, generics.GenericAPIView):
            model = view.serializer_class.Meta.model
        elif hasattr(view, 'permission_model'):
            model = view.permission_model
        else:
            return False

        from dtf.api import ProjectAPIViewMixin
        if not isinstance(view, ProjectAPIViewMixin):
            return False
        project = view.get_project()

        request_operation = _get_requested_operation(request)
        return has_required_model_role(request.user, project, model, request_operation)
