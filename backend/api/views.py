from django.contrib.auth import authenticate, logout
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from users.models import User, Follow
from recipes.models import (
    Recipe, Ingredient, IngredientInRecipe, Favorite, ShoppingCart
)
from .serializers import (
    UserSerializer, UserWithRecipesSerializer, SetAvatarSerializer,
    SetAvatarResponseSerializer, IngredientSerializer, RecipeListSerializer,
    RecipeCreateSerializer, RecipeMinifiedSerializer,
    RecipeGetShortLinkSerializer, SetPasswordSerializer,
    TokenCreateSerializer, TokenGetResponseSerializer,
    CustomUserCreateSerializer, UserRegistrationResponseSerializer, FollowSerializer
)
from .permissions import IsAuthorOrReadOnly
from .pagination import CustomPagination
from .filters import IngredientFilter, RecipeFilter
from django.conf import settings
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.urls import reverse


class CustomUserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        if 're_password' not in data:
            data['re_password'] = data.get('password', '')

        serializer = CustomUserCreateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserRegistrationResponseSerializer(user).data,
            status=status.HTTP_201_CREATED
        )


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'info', 'without_recipes']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], permission_classes=[IsAuthenticated])
    def avatar(self, request):
        if request.method == 'PUT':
            if not request.data.get('avatar'):
                return Response(
                    {'error': 'Поле avatar обязательно'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer = SetAvatarSerializer(
                request.user, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                SetAvatarResponseSerializer(request.user).data,
                status=status.HTTP_200_OK
            )
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = request.user
        following = get_object_or_404(User, id=pk)
        if request.method == 'POST':
            if user == following:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {'errors': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = Follow.objects.create(user=user, following=following)
            serializer = FollowSerializer(follow, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not Follow.objects.filter(user=user, following=following).exists():
            return Response(
                {'errors': 'Подписка не существует'},
                status=status.HTTP_400_BAD_REQUEST
            )
        follow = Follow.objects.get(user=user, following=following)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'], url_path='info', permission_classes=[AllowAny])
    def info(self, request, pk=None):
        user = get_object_or_404(User, id=pk)
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='without_recipes', permission_classes=[AllowAny])
    def without_recipes(self, request):
        users = User.objects.filter(recipes__isnull=True).distinct()
        page = self.paginate_queryset(users)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RecipeFilter

    def get_permissions(self):
        # Все GET-запросы доступны всем
        if self.request.method in ['GET', 'HEAD', 'OPTIONS']:
            return [AllowAny()]
        return [IsAuthorOrReadOnly()]

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateSerializer
        elif self.action in ['favorite', 'shopping_cart']:
            return RecipeMinifiedSerializer
        elif self.action == 'get_link':
            return RecipeGetShortLinkSerializer
        return RecipeListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = self.perform_create(serializer)
        response_serializer = RecipeListSerializer(recipe, context={'request': request})
        headers = self.get_success_headers(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        return serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if recipe.favorites.filter(user=user).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not recipe.favorites.filter(user=user).exists():
            return Response(
                {'errors': 'Рецепт не в избранном'},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite = Favorite.objects.get(user=user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if recipe.in_shopping_cart.filter(user=user).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not recipe.in_shopping_cart.filter(user=user).exists():
            return Response(
                {'errors': 'Рецепт не в списке покупок'},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart = ShoppingCart.objects.get(user=user, recipe=recipe)
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        short_link = f'{settings.BASE_URL}/s/{recipe.id}'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = IngredientInRecipe.objects.filter(
            recipe__in_shopping_cart__user=user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')

        content = '\n'.join([
            f"{item['ingredient__name']} - {item['total_amount']} {item['ingredient__measurement_unit']}"
            for item in ingredients
        ])
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=False, methods=['get'], url_path='filter_by_ingredients')
    def filter_by_ingredients(self, request):
        ingredients_param = request.query_params.get('ingredients')
        if not ingredients_param:
            return Response({'error': 'Необходимо указать параметр ingredients'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ingredient_ids = [int(i) for i in ingredients_param.split(',') if i.strip().isdigit()]
        except ValueError:
            return Response({'error': 'Некорректный формат параметра ingredients'}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.get_queryset().filter(ingredient_in_recipe__ingredient__id__in=ingredient_ids).distinct()
        page = self.paginate_queryset(queryset)
        serializer = RecipeListSerializer(page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class AuthTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = authenticate(request, email=email, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {'auth_token': token.key},
                status=status.HTTP_200_OK
            )
        return Response(
            {'detail': 'Неверные учетные данные'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.auth_token.delete()
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetPasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'Пользователь с таким email не найден'}, status=status.HTTP_404_NOT_FOUND)
        # Генерируем токен (можно хранить в user.profile или в кэше, для простоты — просто строка)
        token = get_random_string(64)
        user.password_reset_token = token
        user.save(update_fields=['password_reset_token'])
        reset_url = f"{settings.BASE_URL}/password-reset-confirm/{user.pk}/{token}/"
        send_mail(
            'Сброс пароля',
            f'Для сброса пароля перейдите по ссылке: {reset_url}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        return Response({'detail': 'Письмо для сброса пароля отправлено'}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, user_id, token):
        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'error': 'Необходимо указать новый пароль'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(id=user_id, password_reset_token=token).first()
        if not user:
            return Response({'error': 'Неверная ссылка или токен'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.password_reset_token = None
        user.save()
        return Response({'detail': 'Пароль успешно изменён'}, status=status.HTTP_200_OK)