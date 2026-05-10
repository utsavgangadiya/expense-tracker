# tracker/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum
from datetime import datetime

class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('Food', 'Food'),
        ('Travel', 'Travel'),
        ('Shopping', 'Shopping'),
        ('Bills', 'Bills'),
        ('Entertainment', 'Entertainment'),
        ('Health', 'Health'),
        ('Education', 'Education'),
        ('Other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    date = models.DateField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.date})"

    class Meta:
        ordering = ['-date']  # Latest first


class Budget(models.Model):
    """Monthly budget tracking for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.CharField(max_length=20, choices=Expense.CATEGORY_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()  # Store first day of month
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'category', 'month']
        ordering = ['-month']
    
    def __str__(self):
        return f"{self.user.username} - {self.category} - {self.month.strftime('%B %Y')}: ${self.amount}"
    
    def get_spent_amount(self):
        """Calculate total spent in this category for this month"""
        month_start = self.month
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1)
        
        spent = Expense.objects.filter(
            user=self.user,
            category=self.category,
            date__gte=month_start,
            date__lt=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return spent
    
    def get_remaining(self):
        """Calculate remaining budget"""
        return self.amount - self.get_spent_amount()
    
    def get_percentage_used(self):
        """Calculate percentage of budget used"""
        spent = self.get_spent_amount()
        if self.amount > 0:
            return (spent / self.amount) * 100
        return 0


class UserProfile(models.Model):
    """Extended user profile information"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    monthly_budget_limit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default='USD')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_total_expenses_this_month(self):
        """Calculate total expenses for current month"""
        now = datetime.now()
        month_start = now.replace(day=1)
        
        total = Expense.objects.filter(
            user=self.user,
            date__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        return total
