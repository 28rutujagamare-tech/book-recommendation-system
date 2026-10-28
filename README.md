# Folio — Book recommendations by genre

A small Django book-discovery app. Readers can enter or choose a genre and browse books curated for that category. Recommendations are ordinary database queries, ordered by featured status, reader rating, and title; **there is no machine learning**.

## Run locally

From this directory, install dependencies and prepare the database:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_books
python manage.py createsuperuser
python manage.py runserver
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) to browse, or [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) to add and edit genres, themes, books, reviews, and user preferences. Readers can create accounts, log in, and leave one review per book; their review can be edited by submitting it again. During signup they can choose favorite genres, authors, themes, language, and book length. Signed-in readers see books matching their choices. Multiple selected genres and themes are matched with AND logic. The seed command is safe to rerun.

Search supports both book titles and genre names. Books can be tagged with multiple genres and themes, and catalog editors can record language and page count for preference matching. Book cover images are displayed with their full proportions instead of being cropped.

## JSON API

`GET /api/recommendations/?genre=Fantasy` returns matching genres and books as JSON. Genre matching is case-insensitive and accepts partial names. A missing genre returns HTTP 400; an unknown genre returns HTTP 404.

## Configuration

For deployment, set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and `DJANGO_ALLOWED_HOSTS` to comma-separated hostnames. The included default secret key and SQLite configuration are for local development only.

## Tests

```powershell
python manage.py test
```
## Author

Rutuja Gamare