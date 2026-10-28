from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


LANGUAGE_CHOICES = [
    ("en", "English"),
    ("hi", "Hindi"),
    ("es", "Spanish"),
    ("fr", "French"),
    ("de", "German"),
    ("it", "Italian"),
    ("pt", "Portuguese"),
    ("ja", "Japanese"),
    ("zh", "Chinese"),
    ("ar", "Arabic"),
]

BOOK_LENGTH_CHOICES = [
    ("short", "Short (up to 200 pages)"),
    ("medium", "Medium (201–400 pages)"),
    ("long", "Long (more than 400 pages)"),
]


def book_length_for_pages(page_count):
    if not page_count:
        return ""
    if page_count <= 200:
        return "short"
    if page_count <= 400:
        return "medium"
    return "long"


class Genre(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.CharField(max_length=240, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "genres"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "genre"
            self.slug = base_slug
            suffix = 2
            while Genre.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{suffix}"
                suffix += 1
        super().save(*args, **kwargs)


class Theme(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True, blank=True)
    author = models.CharField(max_length=120)
    genre = models.ForeignKey(Genre, on_delete=models.PROTECT, related_name="books")
    additional_genres = models.ManyToManyField(
        Genre, blank=True, related_name="additional_books"
    )
    themes = models.ManyToManyField(Theme, blank=True, related_name="books")
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")
    page_count = models.PositiveSmallIntegerField(null=True, blank=True)
    description = models.TextField()
    cover_url = models.URLField(blank=True)
    publication_year = models.PositiveSmallIntegerField(null=True, blank=True)
    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=Decimal("4.0"),
        validators=[MinValueValidator(Decimal("0.0")), MaxValueValidator(Decimal("5.0"))],
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_featured", "-rating", "title"]

    def __str__(self):
        return f"{self.title} — {self.author}"

    def get_absolute_url(self):
        return reverse("catalog:book_detail", args=[self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or "book"
            self.slug = base_slug
            suffix = 2
            while Book.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{suffix}"
                suffix += 1
        super().save(*args, **kwargs)


class Review(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="book_reviews")
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    body = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(fields=["book", "user"], name="unique_review_per_user_book")
        ]

    def __str__(self):
        return f"{self.user} on {self.book}: {self.rating}/5"


class UserPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences"
    )
    favorite_genres = models.ManyToManyField(Genre, blank=True, related_name="fans")
    favorite_authors = models.JSONField(default=list, blank=True)
    preferred_language = models.CharField(
        max_length=2, choices=LANGUAGE_CHOICES, blank=True
    )
    preferred_length = models.CharField(
        max_length=8, choices=BOOK_LENGTH_CHOICES, blank=True
    )
    favorite_themes = models.ManyToManyField(Theme, blank=True, related_name="fans")

    class Meta:
        verbose_name = "user preference"
        verbose_name_plural = "user preferences"

    def __str__(self):
        return f"Reading preferences for {self.user}"
