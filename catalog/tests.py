from django.test import TestCase
from django.urls import reverse

from django.contrib.auth.models import User

from .models import Book, Genre, Review, Theme, UserPreference


class RecommendationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        fantasy = Genre.objects.create(name="Fantasy")
        mystery = Genre.objects.create(name="Mystery")
        adventure = Theme.objects.create(name="Adventure")
        Book.objects.create(
            title="The Star Road",
            author="A. Reader",
            genre=fantasy,
            description="A journey through a world of wonder.",
            rating="4.8",
            is_featured=True,
        )
        Book.objects.create(
            title="The Quiet Case",
            author="B. Writer",
            genre=mystery,
            description="A puzzle waiting to be solved.",
            rating="4.2",
        )
        combined = Book.objects.create(
            title="The Crossed Clues",
            author="A. Reader",
            genre=fantasy,
            description="A romance threaded through a mystery.",
            language="hi",
            page_count=180,
            rating="4.5",
        )
        combined.additional_genres.add(mystery)
        combined.themes.add(adventure)

    def test_home_shows_featured_books_and_genres(self):
        response = self.client.get(reverse("catalog:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Star Road")
        self.assertContains(response, "Fantasy")
        self.assertNotContains(response, "The Quiet Case")

    def test_genre_search_is_case_insensitive(self):
        response = self.client.get(reverse("catalog:home"), {"genre": "fantasy"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Star Road")
        self.assertNotContains(response, "The Quiet Case")

    def test_search_matches_book_title(self):
        response = self.client.get(reverse("catalog:home"), {"q": "Star Road"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Star Road")
        self.assertNotContains(response, "The Quiet Case")

    def test_search_matches_genre(self):
        response = self.client.get(reverse("catalog:home"), {"q": "myst"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Quiet Case")
        self.assertNotContains(response, "The Star Road")

    def test_search_can_match_title_and_genre(self):
        response = self.client.get(reverse("catalog:home"), {"q": "The"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Star Road")
        self.assertContains(response, "The Quiet Case")

    def test_unknown_search_shows_empty_state(self):
        response = self.client.get(reverse("catalog:home"), {"genre": "western"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No books matched")

    def test_api_returns_matching_books(self):
        response = self.client.get(reverse("catalog:recommendations_api"), {"genre": "fant"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["recommendations"][0]["title"], "The Star Road")
        self.assertEqual(response.json()["matched_genres"], ["Fantasy"])

    def test_api_requires_a_genre(self):
        response = self.client.get(reverse("catalog:recommendations_api"))

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_api_returns_not_found_for_unknown_genre(self):
        response = self.client.get(reverse("catalog:recommendations_api"), {"genre": "western"})

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.json())

    def test_book_detail_page(self):
        book = Book.objects.get(title="The Star Road")

        response = self.client.get(reverse("catalog:book_detail", args=[book.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "A journey through a world of wonder.")

    def test_signup_creates_and_logs_in_user(self):
        response = self.client.post(
            reverse("catalog:signup"),
            {
                "username": "reader",
                "email": "reader@example.com",
                "password1": "A-long-test-password-2026!",
                "password2": "A-long-test-password-2026!",
            },
        )

        self.assertRedirects(response, reverse("catalog:home"))
        self.assertTrue(User.objects.filter(username="reader").exists())
        self.assertIn("_auth_user_id", self.client.session)

    def test_signup_saves_selected_reading_preferences(self):
        fantasy = Genre.objects.get(name="Fantasy")
        adventure = Theme.objects.get(name="Adventure")

        response = self.client.post(
            reverse("catalog:signup"),
            {
                "username": "preference_reader",
                "email": "preferences@example.com",
                "password1": "A-long-test-password-2026!",
                "password2": "A-long-test-password-2026!",
                "favorite_genres": [fantasy.pk],
                "favorite_authors": ["A. Reader"],
                "preferred_language": "hi",
                "preferred_length": "short",
                "favorite_themes": [adventure.pk],
            },
        )

        self.assertRedirects(response, reverse("catalog:home"))
        preferences = User.objects.get(username="preference_reader").preferences
        self.assertEqual(list(preferences.favorite_genres.all()), [fantasy])
        self.assertEqual(list(preferences.favorite_themes.all()), [adventure])
        self.assertEqual(preferences.favorite_authors, ["A. Reader"])
        self.assertEqual(preferences.preferred_language, "hi")
        self.assertEqual(preferences.preferred_length, "short")

    def test_signup_form_shows_preference_fields(self):
        response = self.client.get(reverse("catalog:signup"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorite genres")
        self.assertContains(response, "Favorite authors")
        self.assertContains(response, "Preferred language")
        self.assertContains(response, "Preferred length")
        self.assertContains(response, "Favorite themes")

    def test_recommendations_require_every_selected_genre_and_preference(self):
        user = User.objects.create_user(username="picker", password="a-strong-password")
        preferences = UserPreference.objects.create(
            user=user,
            favorite_authors=["A. Reader"],
            preferred_language="hi",
            preferred_length="short",
        )
        preferences.favorite_genres.set(
            [Genre.objects.get(name="Fantasy"), Genre.objects.get(name="Mystery")]
        )
        preferences.favorite_themes.set([Theme.objects.get(name="Adventure")])
        self.client.force_login(user)

        response = self.client.get(reverse("catalog:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The Crossed Clues")
        self.assertNotContains(response, "The Star Road")
        self.assertNotContains(response, "The Quiet Case")
        self.assertContains(response, "Picked for")

    def test_signup_preferences_are_optional(self):
        response = self.client.post(
            reverse("catalog:signup"),
            {
                "username": "casual_reader",
                "email": "casual@example.com",
                "password1": "A-long-test-password-2026!",
                "password2": "A-long-test-password-2026!",
                "favorite_genres": [],
                "favorite_authors": [],
                "preferred_language": "",
                "preferred_length": "",
                "favorite_themes": [],
            },
        )

        self.assertRedirects(response, reverse("catalog:home"))
        self.assertEqual(User.objects.get(username="casual_reader").preferences.favorite_authors, [])

    def test_login_and_logout(self):
        user = User.objects.create_user(username="reader", password="a-strong-password")

        response = self.client.post(
            reverse("catalog:login"),
            {"username": user.username, "password": "a-strong-password"},
        )
        self.assertRedirects(response, reverse("catalog:home"))

        response = self.client.post(reverse("catalog:logout"))
        self.assertRedirects(response, reverse("catalog:home"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_anonymous_review_is_redirected_to_login(self):
        book = Book.objects.get(title="The Star Road")

        response = self.client.post(
            reverse("catalog:submit_review", args=[book.slug]),
            {"rating": 5, "body": "A wonderful read."},
        )

        self.assertRedirects(
            response,
            f"{reverse('catalog:login')}?next={reverse('catalog:submit_review', args=[book.slug])}",
        )
        self.assertEqual(Review.objects.count(), 0)

    def test_authenticated_user_can_create_and_update_one_review(self):
        user = User.objects.create_user(username="reviewer", password="a-strong-password")
        self.client.force_login(user)
        book = Book.objects.get(title="The Star Road")
        url = reverse("catalog:submit_review", args=[book.slug])

        response = self.client.post(url, {"rating": 5, "body": "A wonderful read."})
        self.assertRedirects(response, f"{book.get_absolute_url()}#reviews")
        self.assertEqual(Review.objects.count(), 1)

        response = self.client.post(url, {"rating": 4, "body": "Still a great read."})
        self.assertRedirects(response, f"{book.get_absolute_url()}#reviews")
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.get(book=book, user=user)
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.body, "Still a great read.")

    def test_detail_displays_reader_review(self):
        book = Book.objects.get(title="The Star Road")
        user = User.objects.create_user(username="reviewer", password="a-strong-password")
        Review.objects.create(book=book, user=user, rating=5, body="A wonderful read.")

        response = self.client.get(book.get_absolute_url())

        self.assertContains(response, "Reader reviews")
        self.assertContains(response, "A wonderful read.")
        self.assertContains(response, "reviewer")
