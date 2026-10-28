from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import ReviewForm, SignUpForm
from .models import Book, Genre, Review, UserPreference


def _matching_genres(query):
    exact_match = Genre.objects.filter(name__iexact=query)
    if exact_match.exists():
        return exact_match
    return Genre.objects.filter(name__icontains=query)


def _books_for_preferences(preferences):
    books = Book.objects.select_related("genre").prefetch_related(
        "additional_genres", "themes"
    ).all()

    selected_genres = list(preferences.favorite_genres.all())
    for genre in selected_genres:
        books = books.filter(Q(genre=genre) | Q(additional_genres=genre))

    if preferences.favorite_authors:
        books = books.filter(author__in=preferences.favorite_authors)
    if preferences.preferred_language:
        books = books.filter(language=preferences.preferred_language)
    if preferences.preferred_length == "short":
        books = books.filter(page_count__lte=200, page_count__isnull=False)
    elif preferences.preferred_length == "medium":
        books = books.filter(page_count__gte=201, page_count__lte=400)
    elif preferences.preferred_length == "long":
        books = books.filter(page_count__gt=400)
    for theme in preferences.favorite_themes.all():
        books = books.filter(themes=theme)
    return books.distinct()


def home(request):
    query = request.GET.get("q", request.GET.get("genre", "")).strip()
    genres = Genre.objects.all()
    books = Book.objects.select_related("genre").prefetch_related(
        "additional_genres", "themes"
    ).all()
    selected_genres = Genre.objects.filter(name__icontains=query) if query else Genre.objects.none()
    is_search = bool(query)
    personalized = False
    preferences = None

    if is_search:
        books = books.filter(
            Q(title__icontains=query)
            | Q(genre__name__icontains=query)
            | Q(additional_genres__name__icontains=query)
        ).distinct()
    elif request.user.is_authenticated:
        try:
            preferences = request.user.preferences
        except UserPreference.DoesNotExist:
            preferences = None
        if preferences and (
            preferences.favorite_genres.exists()
            or preferences.favorite_authors
            or preferences.preferred_language
            or preferences.preferred_length
            or preferences.favorite_themes.exists()
        ):
            books = _books_for_preferences(preferences)
            personalized = True
        else:
            books = books.filter(is_featured=True)
    else:
        books = books.filter(is_featured=True)

    return render(
        request,
        "catalog/home.html",
        {
            "genres": genres,
            "books": books,
            "query": query,
            "selected_genres": selected_genres,
            "is_search": is_search,
            "personalized": personalized,
            "result_count": books.count() if is_search or personalized else 0,
        },
    )


def book_detail(request, slug):
    book = get_object_or_404(
        Book.objects.select_related("genre").prefetch_related("additional_genres", "themes"),
        slug=slug,
    )
    review = None
    if request.user.is_authenticated:
        review = Review.objects.filter(book=book, user=request.user).first()
    return _render_book_detail(request, book, ReviewForm(instance=review))


def _render_book_detail(request, book, review_form):
    reviews = book.reviews.select_related("user").all()
    more_from_genre = (
        Book.objects.filter(genre=book.genre)
        .exclude(pk=book.pk)
        .select_related("genre")[:3]
    )
    return render(
        request,
        "catalog/book_detail.html",
        {
            "book": book,
            "more_from_genre": more_from_genre,
            "review_form": review_form,
            "reviews": reviews,
            "review_count": reviews.count(),
        },
    )


@login_required
def submit_review(request, slug):
    if request.method != "POST":
        return redirect("catalog:book_detail", slug=slug)

    book = get_object_or_404(Book, slug=slug)
    review = Review.objects.filter(book=book, user=request.user).first()
    form = ReviewForm(request.POST, instance=review)
    if form.is_valid():
        saved_review = form.save(commit=False)
        saved_review.book = book
        saved_review.user = request.user
        saved_review.save()
        messages.success(request, "Your review has been saved.")
    else:
        messages.error(request, "Please correct the errors in your review.")
        reviews = book.reviews.select_related("user").all()
        more_from_genre = (
            Book.objects.filter(genre=book.genre)
            .exclude(pk=book.pk)
            .select_related("genre")[:3]
        )
        return render(
            request,
            "catalog/book_detail.html",
            {
                "book": book,
                "more_from_genre": more_from_genre,
                "review_form": form,
                "reviews": reviews,
                "review_count": reviews.count(),
            },
        )
    return redirect(f"{book.get_absolute_url()}#reviews")


def signup(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Welcome to Folio!")
        return redirect("catalog:home")
    return render(request, "registration/signup.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("catalog:home")
    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        next_url = request.POST.get("next") or request.GET.get("next", "")
        if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("catalog:home")
    return render(
        request,
        "registration/login.html",
        {"form": form, "next": request.POST.get("next") or request.GET.get("next", "")},
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been signed out.")
    return redirect("catalog:home")


def recommendations_api(request):
    query = request.GET.get("genre", "").strip()
    if not query:
        return JsonResponse(
            {"error": "Add a genre query parameter, for example ?genre=fantasy."},
            status=400,
        )

    genres = _matching_genres(query)
    if not genres.exists():
        return JsonResponse(
            {"error": f'No book genre matches “{query}”.', "genre": query},
            status=404,
        )

    books = (
        Book.objects.filter(Q(genre__in=genres) | Q(additional_genres__in=genres))
        .select_related("genre")
        .prefetch_related("additional_genres")
        .distinct()
    )
    return JsonResponse(
        {
            "genre": query,
            "matched_genres": [genre.name for genre in genres],
            "recommendations": [
                {
                    "title": book.title,
                    "author": book.author,
                    "genre": book.genre.name,
                    "genres": [book.genre.name, *[genre.name for genre in book.additional_genres.all()]],
                    "language": book.get_language_display(),
                    "page_count": book.page_count,
                    "themes": [theme.name for theme in book.themes.all()],
                    "description": book.description,
                    "publication_year": book.publication_year,
                    "rating": str(book.rating),
                    "url": request.build_absolute_uri(book.get_absolute_url()),
                }
                for book in books
            ],
        }
    )
