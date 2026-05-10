from django.contrib import admin
from .models import Expense, Budget, UserProfile

# Register your models here.

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'amount', 'category', 'date', 'created_at']
    list_filter = ['category', 'date', 'user']
    search_fields = ['title', 'description', 'user__email']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'amount', 'month']
    list_filter = ['category', 'month', 'user']
    search_fields = ['user__email']
    ordering = ['-month']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'monthly_budget_limit', 'currency', 'created_at']
    search_fields = ['user__email', 'user__username']
    list_filter = ['currency']
