from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, RecipeViewSet, IngredientViewSet,
    AuthTokenView, LogoutView, SetPasswordView, CustomUserRegistrationView,
    PasswordResetRequestView, PasswordResetConfirmView
)

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipes')
router.register(r'ingredients', IngredientViewSet, basename='ingredients')
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/token/login/', AuthTokenView.as_view(), name='token_login'),
    path('auth/token/logout/', LogoutView.as_view(), name='token_logout'),
    path('users/set_password/', SetPasswordView.as_view(), name='set_password'),
    path('users/', CustomUserRegistrationView.as_view(), name='custom-user-register'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset-confirm/<int:user_id>/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/', include('social_django.urls', namespace='social')),
]