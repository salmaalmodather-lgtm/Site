from django.urls import path
from . import views

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("", views.dashboard_redirect, name="dashboard_redirect"),
    path("add-teacher/", views.add_teacher, name="add_teacher"),
    path("dashboard/", views.dashboard, name="dashboard"),

    path("api/items/", views.api_list_items, name="api_list_items"),
    path("api/items/create/", views.api_create_item, name="api_create_item"),
    path("api/items/<int:item_id>/", views.api_update_item, name="api_update_item"),
    path("api/items/<int:item_id>/delete/", views.api_delete_item, name="api_delete_item"),
    path("api/items/reset/", views.api_reset_items, name="api_reset_items"),
]
