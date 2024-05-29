from django.urls import path
from orders import views

urlpatterns = [
    path('dataFeeder', views.dataFeeder),
]
