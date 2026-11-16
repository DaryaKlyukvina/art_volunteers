"""Пользовательские валидаторы-функции для полей форм и моделей."""
from django.core.exceptions import ValidationError


def validate_has_letters(value):
    """Название должно содержать хотя бы одну букву (не только цифры и знаки)."""
    if not any(char.isalpha() for char in value):
        raise ValidationError("Название должно содержать буквы, а не только цифры и знаки.")


def validate_image_size(image, max_mb=3):
    """Ограничение размера загружаемого изображения."""
    if image and image.size > max_mb * 1024 * 1024:
        raise ValidationError(f"Размер изображения не должен превышать {max_mb} МБ.")
