from rest_framework.permissions import BasePermission
from ..views import kite

class CustomPermission(BasePermission):
    def has_permission(self, request, view):
        if kite.access_token:
            return True
        else:
            return False
    