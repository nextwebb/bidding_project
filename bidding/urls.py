from django.urls import path
from . import views

urlpatterns = [
    path('bid/', views.bid_endpoint, name='bid_endpoint'),
]
