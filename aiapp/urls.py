from django.urls import path, include
from . import views

urlpatterns = [
    path('feedback/', views.feedback, name='feedback'),
    path('summary/', views.summary, name='summary'),
    path('sentiment/', views.sentiment, name='sentiment'),
]
