from django.core.management.base import BaseCommand

from catalog.models import Book, Genre, Theme


BOOKS = {
    "Fantasy": [
        ("The Hobbit", "J.R.R. Tolkien", 1937, "A home-loving hobbit joins a company of dwarves on a bold quest to reclaim their mountain home.", "4.8"),
        ("A Wizard of Earthsea", "Ursula K. Le Guin", 1968, "A gifted young wizard learns that true power begins with knowing the names of things.", "4.7"),
        ("The Night Circus", "Erin Morgenstern", 2011, "Two young illusionists are bound to a mysterious competition staged inside a traveling circus.", "4.4"),
        ("The Last Unicorn", "Peter S. Beagle", 1968, "A unicorn leaves her enchanted forest to discover what became of the others of her kind.", "4.5"),
    ],
    "Mystery": [
        ("The Thursday Murder Club", "Richard Osman", 2020, "Four sharp-minded retirement-home residents investigate a killing close to home.", "4.3"),
        ("The Hound of the Baskervilles", "Arthur Conan Doyle", 1902, "Sherlock Holmes investigates a chilling legend surrounding a family estate on the moors.", "4.5"),
        ("The Murder of Roger Ackroyd", "Agatha Christie", 1926, "Hercule Poirot returns to a quiet village to untangle a baffling and closely guarded case.", "4.6"),
        ("The No. 1 Ladies' Detective Agency", "Alexander McCall Smith", 1998, "Precious Ramotswe opens Botswana's first women-run detective agency.", "4.2"),
        ("The Inheritance Games", "Jennifer Lynn Barnes", 2020, "A teenager inherits a fortune and must solve a family's elaborate puzzles to uncover why.", "4.4"),
    ],
    "Science Fiction": [
        ("Dune", "Frank Herbert", 1965, "A young heir is drawn into the politics and ecology of a desert planet rich in a precious spice.", "4.6"),
        ("Kindred", "Octavia E. Butler", 1979, "A modern Black woman is repeatedly pulled back in time to a Maryland plantation.", "4.7"),
        ("The Left Hand of Darkness", "Ursula K. Le Guin", 1969, "An envoy visits a world whose inhabitants can change gender, challenging his assumptions about humanity.", "4.4"),
        ("Project Hail Mary", "Andy Weir", 2021, "An astronaut wakes alone aboard a spacecraft with one chance to save Earth.", "4.6"),
    ],
    "Romance": [
        ("Pride and Prejudice", "Jane Austen", 1813, "Elizabeth Bennet and Mr. Darcy challenge each other's pride and first impressions.", "4.6"),
        ("Book Lovers", "Emily Henry", 2022, "A literary agent and an editor keep crossing paths during an unexpectedly revealing summer.", "4.2"),
        ("The Kiss Quotient", "Helen Hoang", 2018, "A data-minded woman hires an escort to help her navigate dating and discovers an unexpected connection.", "4.1"),
        ("Jane Eyre", "Charlotte Brontë", 1847, "An independent governess finds love, purpose, and a secret at Thornfield Hall.", "4.5"),
    ],
    "Historical Fiction": [
        ("All the Light We Cannot See", "Anthony Doerr", 2014, "A blind French girl and a German boy find their paths crossing during World War II.", "4.5"),
        ("The Book Thief", "Markus Zusak", 2005, "A young girl in wartime Germany discovers the power of words and small acts of kindness.", "4.6"),
        ("Homegoing", "Yaa Gyasi", 2016, "Two half-sisters' descendants trace a sweeping family story across Ghana and America.", "4.5"),
        ("The Pillars of the Earth", "Ken Follett", 1989, "Builders, nobles, and villagers shape a cathedral and their lives in medieval England.", "4.4"),
    ],
}

THEMES_BY_GENRE = {
    "Fantasy": ("Magic", "Adventure"),
    "Mystery": ("Puzzles", "Family secrets"),
    "Science Fiction": ("Space", "Technology"),
    "Romance": ("Love", "Second chances"),
    "Historical Fiction": ("Family", "Resilience"),
}

ADDITIONAL_GENRES = {
    "The Night Circus": ("Romance",),
    "The Inheritance Games": ("Romance",),
}

PAGE_COUNTS = {
    "The Hobbit": 310,
    "A Wizard of Earthsea": 205,
    "The Night Circus": 512,
    "The Last Unicorn": 294,
    "The Thursday Murder Club": 368,
    "The Hound of the Baskervilles": 256,
    "The Murder of Roger Ackroyd": 288,
    "The No. 1 Ladies' Detective Agency": 240,
    "The Inheritance Games": 384,
    "Dune": 688,
    "Kindred": 288,
    "The Left Hand of Darkness": 304,
    "Project Hail Mary": 496,
    "Pride and Prejudice": 432,
    "Book Lovers": 384,
    "The Kiss Quotient": 336,
    "Jane Eyre": 532,
    "All the Light We Cannot See": 544,
    "The Book Thief": 584,
    "Homegoing": 320,
    "The Pillars of the Earth": 973,
}

DESCRIPTIONS = {
    "Fantasy": "Step into an imaginative world of magic, myth, and unforgettable journeys.",
    "Mystery": "Follow the clues through a clever puzzle, a hidden secret, or an unexpected crime.",
    "Science Fiction": "Explore bold ideas about technology, society, and possible futures.",
    "Romance": "Find heartfelt stories about connection, chemistry, and love in all its forms.",
    "Historical Fiction": "Discover vivid stories that bring another time and place to life.",
}


class Command(BaseCommand):
    help = "Add a starter set of genres and books to the catalog."

    def handle(self, *args, **options):
        created_books = 0
        genres = {}
        for genre_name, books in BOOKS.items():
            genre, _ = Genre.objects.get_or_create(
                name=genre_name,
                defaults={"description": DESCRIPTIONS[genre_name]},
            )
            genres[genre_name] = genre
        for genre_name, books in BOOKS.items():
            genre = genres[genre_name]
            for title, author, year, description, rating in books:
                book, created = Book.objects.update_or_create(
                    title=title,
                    defaults={
                        "author": author,
                        "genre": genre,
                        "language": "en",
                        "page_count": PAGE_COUNTS[title],
                        "publication_year": year,
                        "description": description,
                        "rating": rating,
                        "is_featured": title in ("The Hobbit", "The Thursday Murder Club", "Dune", "Pride and Prejudice"),
                    },
                )
                book.additional_genres.set(
                    [genres[name] for name in ADDITIONAL_GENRES.get(title, ())]
                )
                theme_names = THEMES_BY_GENRE[genre_name]
                if title == "The Inheritance Games":
                    theme_names = ("Puzzles", "Family secrets", "Love")
                book.themes.set(
                    [Theme.objects.get_or_create(name=name)[0] for name in theme_names]
                )
                created_books += int(created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Starter catalog ready: {len(BOOKS)} genres, {created_books} new books."
            )
        )
