from django.urls import path

from . import views


app_name = "catalog"

urlpatterns = [
    path("", views.home, name="home"),
    path("accounts/signup/", views.signup, name="signup"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    path("books/<slug:slug>/review/", views.submit_review, name="submit_review"),
    path("books/<slug:slug>/", views.book_detail, name="book_detail"),
    path("api/recommendations/", views.recommendations_api, name="recommendations_api"),
]
