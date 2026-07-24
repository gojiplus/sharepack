from django.urls import path
from . import views

urlpatterns = [
    path("", views.task_list, name="task_list"),
    path("task/<int:pk>/", views.task_detail, name="task_detail"),
    path("task/<int:pk>/toggle/", views.task_toggle, name="task_toggle"),
    path("task/<int:pk>/delete/", views.task_delete, name="task_delete"),
]
