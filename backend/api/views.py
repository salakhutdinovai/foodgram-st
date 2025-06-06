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
    Recipe, Ingredient, Tag, IngredientInRecipe, Favorite, ShoppingCart
)
from .serializers import (
    UserSerializer, UserWithRecipesSerializer, SetAvatarSerializer,
    SetAvatarResponseSerializer, IngredientSerializer, RecipeListSerializer,
    RecipeCreateSerializer, RecipeMinifiedSerializer,
    RecipeGetShortLinkSerializer, SetPasswordSerializer,
    TokenCreateSerializer, TokenGetResponseSerializer, TagSerializer,
    CustomUserCreateSerializer
)
from .permissions import IsAuthorOrReadOnly
from .pagination import CustomPagination
from .filters import IngredientFilter, RecipeFilter

# New registration view
class CustomUserRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("Debug: CustomUserRegistrationView POST called")
        print(f"Debug: Request data: {request.data}")
        
        data = request.data.copy()
        if 're_password' not in data:
            data['re_password'] = data.get('password', '')
            print(f"Debug: Added re_password: {data['re_password']}")

        serializer = CustomUserCreateSerializer(data=data)
        if serializer.is_valid():
            print("Debug: Serializer is valid")
            print(f"Debug: Validated data: {serializer.validated_data}")
            user = serializer.save()
            print(f"Debug: User created: {user}")
            print(f"Debug: User password: {user.password}")
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED
            )
        print(f"Debug: Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.action in ['create', 'list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], permission_classes=[IsAuthenticated])
    def avatar(self, request):
        if request.method == 'PUT':
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
                    {'errors': 'Нельзя подписаться на себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if Follow.objects.filter(user=user, following=following).exists():
                return Response(
                    {'errors': 'Уже подписаны'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Follow.objects.create(user=user, following=following)
            serializer = UserWithRecipesSerializer(
                following, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        follow = get_object_or_404(Follow, user=user, following=following)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeCreateSerializer
        elif self.action in ['favorite', 'shopping_cart']:
            return RecipeMinifiedSerializer
        elif self.action == 'get_link':
            return RecipeGetShortLinkSerializer
        return RecipeListSerializer

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            recipe = self.perform_create(serializer)
            response_serializer = RecipeListSerializer(recipe, context={'request': request})
            headers = self.get_success_headers(serializer.data)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        except Exception as e:
            print(f"Debug: Ошибка при создании рецепта: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        return serializer.save()

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data)
        except Exception as e:
            print(f"Debug: Error updating recipe: {str(e)}")  # Debug
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = get_object_or_404(Favorite, user=user, recipe=recipe)
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        cart = get_object_or_404(ShoppingCart, user=user, recipe=recipe)
        cart.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        short_link = f'https://foodgram.example.org/s/{recipe.id}'
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


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class AuthTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        print(f"Debug: Received data: email={email}, password={password}")  # Debug
        user = authenticate(request, email=email, password=password)
        if user:
            print(f"Debug: User found: {user}")  # Debug
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {'auth_token': token.key},
                status=status.HTTP_200_OK
            )
        print("Debug: User not found or invalid password")  # Debug
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
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(
            serializer.validated_data['current_password']
        ):
            return Response(
                {'current_password': 'Неверный пароль'},
                status=status.HTTP_400_BAD_REQUEST
            )
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)