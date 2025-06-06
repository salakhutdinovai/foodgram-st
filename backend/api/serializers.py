import base64
import uuid
from django.core.files.base import ContentFile
from rest_framework import serializers
from users.models import User, Follow
from recipes.models import (
    Recipe, Ingredient, Tag, IngredientInRecipe, Favorite, ShoppingCart
)


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if data is None:
            return None
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                file_name = f'{uuid.uuid4()}.{ext}'
                data = ContentFile(base64.b64decode(imgstr), name=file_name)
            except Exception as e:
                raise serializers.ValidationError(f'Некорректный формат изображения: {str(e)}')
        return super().to_internal_value(data)


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, following=obj).exists()


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        recipes = obj.recipes.all()
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeMinifiedSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class CustomUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    re_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 're_password')
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'password': {'write_only': True},
            're_password': {'write_only': True},
        }

    def validate(self, data):
        print("Debug: validate method called")
        print(f"Debug: received data: {data}")
        if 're_password' in data and data['password'] != data['re_password']:
            raise serializers.ValidationError({'re_password': 'Пароли не совпадают'})
        data['email'] = data['email'].lower()
        for field in ['email', 'username', 'first_name', 'last_name', 'password']:
            if field not in data or not data[field]:
                raise serializers.ValidationError({field: f'Поле {field} обязательно'})
        return data

    def create(self, validated_data):
        print("Debug: create method called")
        print(f"Debug: validated_data: {validated_data}")
        
        validated_data.pop('re_password', None)
        password = validated_data.get('password')
        print(f"Debug: password to be set: {password}")
        
        try:
            user = User.objects.create_user(
                email=validated_data['email'],
                username=validated_data['username'],
                first_name=validated_data['first_name'],
                last_name=validated_data['last_name'],
                password=password
            )
            print(f"Debug: user created: {user}")
            print(f"Debug: user password in db: {user.password}")
            print(f"Debug: password is usable: {user.has_usable_password()}")
            return user
        except Exception as e:
            print(f"Debug: Error creating user: {str(e)}")
            raise serializers.ValidationError(f"Ошибка при создании пользователя: {str(e)}")
        

class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeListSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        source='ingredient_in_recipe', many=True, read_only=True
    )
    tags = serializers.SlugRelatedField(
        slug_field='slug', queryset=Tag.objects.all(), many=True
    )
    image = Base64ImageField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        )
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False
    )
    image = Base64ImageField(required=False)
    name = serializers.CharField(required=True, max_length=256)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(required=True, min_value=1)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = ('ingredients', 'tags', 'image', 'name', 'text', 'cooking_time', 'author')

    def validate(self, data):
        if self.context['request'].method == 'POST' and not data.get('image'):
            raise serializers.ValidationError({'image': 'Изображение обязательно при создании рецепта'})
        if not data.get('name'):
            raise serializers.ValidationError({'name': 'Название обязательно'})
        if not data.get('text'):
            raise serializers.ValidationError({'text': 'Описание обязательно'})
        if not data.get('cooking_time'):
            raise serializers.ValidationError({'cooking_time': 'Время приготовления обязательно'})
        if data.get('cooking_time') < 1:
            raise serializers.ValidationError({'cooking_time': 'Время приготовления должно быть больше 0'})
        return data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Ингредиенты обязательны.')
        ingredient_ids = [item['id'] for item in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты не должны повторяться.')
        for item in value:
            if item['amount'] < 1:
                raise serializers.ValidationError(
                    {'amount': 'Количество должно быть >= 1.'}
                )
        return value

    def create_ingredients(self, recipe, ingredients_data):
        IngredientInRecipe.objects.bulk_create([
            IngredientInRecipe(
                recipe=recipe,
                ingredient_id=data['id'],
                amount=data['amount']
            ) for data in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags = validated_data.pop('tags', [])
        recipe = Recipe.objects.create(author=self.context['request'].user, **validated_data)
        if tags:
            recipe.tags.set(tags)
        self.create_ingredients(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if tags is not None and isinstance(tags, (list, tuple)):
            try:
                instance.tags.set(tags)
            except Exception as e:
                print(f"Debug: Ошибка при установке tags: {str(e)}")
                pass

        if ingredients_data:
            instance.ingredient_in_recipe.all().delete()
            self.create_ingredients(instance, ingredients_data)

        return instance

    def to_representation(self, instance):
        return RecipeListSerializer(instance, context=self.context).data


class RecipeGetShortLinkSerializer(serializers.Serializer):
    short_link = serializers.URLField()


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    current_password = serializers.CharField()


class TokenCreateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            raise serializers.ValidationError(
                'Необходимо указать email и пароль.'
            )
        return data


class TokenGetResponseSerializer(serializers.Serializer):
    auth_token = serializers.CharField()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')