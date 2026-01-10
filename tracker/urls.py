# tracker/urls.py
from django.urls import path
from . import views
from .views import export_expenses_pdf
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.expense_list, name='expense_list'),
    path('add/', views.add_expense, name='add_expense'),
    path('edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('export-pdf/', export_expenses_pdf, name='export_pdf'),

   
]