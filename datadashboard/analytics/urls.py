from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_data, name='upload_data'),
    path('summary/', views.summary, name='summary'),
    path('charts/', views.charts, name='charts'),
]
