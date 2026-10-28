from django.contrib import admin

from .models import Book, Genre, Review, Theme, UserPreference


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "genre", "language", "page_count", "rating", "publication_year", "is_featured")
    list_filter = ("genre", "additional_genres", "themes", "language", "is_featured", "publication_year")
    search_fields = ("title", "author", "description")
    list_editable = ("rating", "is_featured")
    autocomplete_fields = ("genre",)
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("additional_genres", "themes")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "updated_at")
    list_filter = ("rating", "updated_at")
    search_fields = ("book__title", "user__username", "body")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "preferred_language", "preferred_length")
    search_fields = ("user__username", "favorite_authors")
    filter_horizontal = ("favorite_genres", "favorite_themes")
