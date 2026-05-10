# tracker/urls.py
from django.urls import path
from . import views
from django.shortcuts import redirect

urlpatterns = [
    path('', views.expense_list, name='expense_list'),
    path('add/', views.add_expense, name='add_expense'),
    path('edit/<int:pk>/', views.edit_expense, name='edit_expense'),
    path('delete/<int:pk>/', views.delete_expense, name='delete_expense'),
    path('export-pdf/', views.export_expenses_pdf, name='export_pdf'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('budget/', views.budget_view, name='budget'),
    path('budget/add/', views.add_budget, name='add_budget'),
    path('budget/edit/<int:pk>/', views.edit_budget, name='edit_budget'),
    path('budget/delete/<int:pk>/', views.delete_budget, name='delete_budget'),

    path('login/', lambda request: redirect('/accounts/google/login/'), name='custom_login'),
]
