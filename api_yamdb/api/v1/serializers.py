"""Модуль сериализаторов проекта."""
from django.shortcuts import get_object_or_404

from rest_framework import serializers

from reviews.models import Category, Comment, Genre, Review, Title
from users.models import ROLE_CHOICES, CustomUser


class GenreSerializer(serializers.ModelSerializer):
    """Сериализатор для модели жанров."""

    class Meta:
        model = Genre
        fields = ('name', 'slug')


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для модели категорий."""

    class Meta:
        model = Category
        fields = ('name', 'slug')


class TitleGETSerializer(serializers.ModelSerializer):
    """Сериализатор для модели произведений при GET-запросе."""

    genre = GenreSerializer(many=True, required=False)
    category = CategorySerializer()
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'rating', 'description', 'genre', 'category')
        read_only_fields = fields


class TitleSerializer(serializers.ModelSerializer):
    """Сериализатор для модели произведений при небезопасном запросе."""

    genre = serializers.SlugRelatedField(
        slug_field='slug', queryset=Genre.objects.all(),
        many=True, required=False)
    category = serializers.SlugRelatedField(
        slug_field='slug', queryset=Category.objects.all())

    class Meta:
        model = Title
        fields = (
            'id', 'name', 'year', 'description', 'genre', 'category')


class UserSignUpSerializer(serializers.ModelSerializer):
    """Класс сериализатора для регистрации пользователя."""

    class Meta:
        model = CustomUser
        fields = ('username', 'email',)

    def validate(self, data):
        """Метод для проведения всех необходимых проверок."""

        username = data.get('username')
        email = data.get('email')

        if not data:
            raise serializers.ValidationError(
                {'email': ['Это обязательное поле.'], 'username': [
                    'Это обязательное поле.']})
        if not username:
            raise serializers.ValidationError(
                {'username': ['Это обязательное поле.'], })
        if not email:
            raise serializers.ValidationError(
                {'email': ['Это обязательное поле.'], })
        if username == 'me':
            raise serializers.ValidationError('Выберите другое имя.')
        return data


class UserSerializer(serializers.ModelSerializer):
    """Класс сериализатора для пользователя."""

    role = serializers.ChoiceField(
        choices=ROLE_CHOICES, required=False, read_only=True
    )
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password',
                  'first_name', 'last_name', 'bio', 'role',)


class AdminSerializer(serializers.ModelSerializer):
    """Класс сериализатора для админа."""

    role = serializers.ChoiceField(
        choices=ROLE_CHOICES, required=False,
    )
    is_staff = serializers.BooleanField(
        required=False,
        write_only=True,
    )
    password = serializers.CharField(
        max_length=128,
        min_length=8,
        write_only=True,
        required=False,
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'is_staff', 'password',
                  'first_name', 'last_name', 'bio', 'role',)


class CommentSerializer(serializers.ModelSerializer):
    """Класс сериализатора для комментариев."""

    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    review = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        fields = '__all__'
        model = Comment


class ReviewSerializer(serializers.ModelSerializer):
    """Класс сериализатора для отзывов."""

    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field='username'
    )
    score = serializers.IntegerField()
    title = serializers.PrimaryKeyRelatedField(read_only=True)

    def validate_score(self, value):
        """Метод для для валидации оценки."""
        if value < 1 or value > 10:
            raise serializers.ValidationError(
                'Оценка должна быть в диапазоне от 1 до 10.'
            )
        return value

    def validate(self, value):
        """Метод для для проверки существования отзыва."""
        author = self.context['request'].user
        title_id = (self.context['request'].
                    parser_context['kwargs'].get('title_id'))
        title = get_object_or_404(
            Title,
            id=title_id
        )
        if (self.context['request'].method == 'POST'
                and title.reviews.filter(author=author).exists()):
            raise serializers.ValidationError(
                f'Отзыв на произведение {title.name} уже существует'
            )
        return value

    class Meta:
        fields = '__all__'
        model = Review
