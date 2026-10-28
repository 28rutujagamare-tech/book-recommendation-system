from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import (
    BOOK_LENGTH_CHOICES,
    LANGUAGE_CHOICES,
    Book,
    Genre,
    Review,
    Theme,
    UserPreference,
)


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    favorite_genres = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="A book must match every genre you select.",
    )
    favorite_authors = forms.MultipleChoiceField(
        choices=(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    preferred_language = forms.ChoiceField(
        choices=[("", "No preference"), *LANGUAGE_CHOICES], required=False
    )
    preferred_length = forms.ChoiceField(
        choices=[("", "No preference"), *BOOK_LENGTH_CHOICES], required=False
    )
    favorite_themes = forms.ModelMultipleChoiceField(
        queryset=Theme.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Books must match every theme you select.",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["favorite_genres"].queryset = Genre.objects.order_by("name")
        self.fields["favorite_themes"].queryset = Theme.objects.order_by("name")
        authors = (
            Book.objects.order_by("author")
            .values_list("author", flat=True)
            .distinct()
        )
        self.fields["favorite_authors"].choices = [(author, author) for author in authors]

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            preferences = UserPreference.objects.create(
                user=user,
                favorite_authors=self.cleaned_data["favorite_authors"],
                preferred_language=self.cleaned_data["preferred_language"],
                preferred_length=self.cleaned_data["preferred_length"],
            )
            preferences.favorite_genres.set(self.cleaned_data["favorite_genres"])
            preferences.favorite_themes.set(self.cleaned_data["favorite_themes"])
        return user


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "body")
        widgets = {
            "rating": forms.Select(
                choices=[(rating, f"{rating} out of 5") for rating in range(5, 0, -1)]
            ),
            "body": forms.Textarea(
                attrs={"rows": 4, "placeholder": "What did you think of this book?"}
            ),
        }
