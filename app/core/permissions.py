from django.conf import settings
from rest_framework.permissions import BasePermission


class HasAPIKey(BasePermission):
    """
    Permission class that checks for the presence of a valid API key in the request.
    """
    def has_permission(self, request, view):
        api_key = request.META.get("HTTP_X_API_KEY")
        return api_key == settings.SECRET_API_KEY
