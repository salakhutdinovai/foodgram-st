from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, RecipeViewSet, IngredientViewSet, TagViewSet,
    AuthTokenView, LogoutView, SetPasswordView, CustomUserRegistrationView
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'tags', TagViewSet, basename='tags')


user_viewset_urls = [
    path('users/<int:pk>/', UserViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    }), name='user-detail'),
    path('users/', UserViewSet.as_view({'get': 'list'}), name='user-list'),
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    path('users/me/avatar/', UserViewSet.as_view({'put': 'avatar', 'delete': 'avatar'}), name='user-avatar'),
    path('users/subscriptions/', UserViewSet.as_view({'get': 'subscriptions'}), name='user-subscriptions'),
    path('users/<int:pk>/subscribe/', UserViewSet.as_view({'post': 'subscribe', 'delete': 'subscribe'}), name='user-subscribe'),
]

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', AuthTokenView.as_view(), name='token_login'),
    path('auth/token/logout/', LogoutView.as_view(), name='token_logout'),
    path('users/set_password/', SetPasswordView.as_view(), name='set_password'),
    path('users/', CustomUserRegistrationView.as_view(), name='custom-user-register'),
] + user_viewset_urls