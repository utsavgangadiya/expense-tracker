# tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import Expense, Budget, UserProfile
from .forms import ExpenseForm, BudgetForm
from django.utils.timezone import now 
from datetime import timedelta, datetime
from django.template.loader import get_template
from django.http import HttpResponse, JsonResponse
from xhtml2pdf import pisa
from django.contrib.auth.decorators import login_required
from django.db.models.functions import TruncMonth
import json


@login_required
def expense_list(request):
    # Filter expenses by current user
    expenses = Expense.objects.filter(user=request.user)

    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category = request.GET.get('category')

    if start_date:
        expenses = expenses.filter(date__gte=start_date)
    if end_date:
        expenses = expenses.filter(date__lte=end_date)
    if category and category != 'All':
        expenses = expenses.filter(category=category)

    total = expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    categories = [choice[0] for choice in Expense.CATEGORY_CHOICES]

    # ---- LAST 7 TRANSACTIONS SUMMARY ----
    ordered_expenses = expenses.order_by('-date')
    last_7 = ordered_expenses[:7]

    if last_7.exists():
        last_7_total = sum(e.amount for e in last_7)
        last_7_highest = max(last_7, key=lambda e: e.amount)
        last_7_lowest = min(last_7, key=lambda e: e.amount)
        last_7_avg = last_7_total / last_7.count()
    else:
        last_7_total = 0
        last_7_highest = None
        last_7_lowest = None
        last_7_avg = 0

    # Get user profile or create if doesn't exist
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Calculate this month's total
    now_date = datetime.now()
    month_start = now_date.replace(day=1)
    month_total = Expense.objects.filter(
        user=request.user,
        date__gte=month_start
    ).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'expenses': expenses,
        'total': total,
        'start_date': start_date,
        'end_date': end_date,
        'selected_category': category,
        'categories': categories,

        # LAST 7 SUMMARY DATA
        'last_7': last_7,
        'last_7_total': last_7_total,
        'last_7_highest': last_7_highest,
        'last_7_avg': last_7_avg,
        'last_7_lowest': last_7_lowest,
        
        # Monthly data
        'month_total': month_total,
        'user_profile': profile,
    }

    return render(request, 'tracker/expense_list.html', context)


@login_required
def export_expenses_pdf(request):
    expenses = Expense.objects.filter(user=request.user).order_by('-date')

    template_path = 'tracker/pdf_template.html'
    context = {'expenses': expenses, 'user': request.user}

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expenses.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response


@login_required
def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.user = request.user  # Assign current user
            expense.save()
            messages.success(request, '✅ Expense added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/add_expense.html', {'form': form})


@login_required
def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)  # Ensure user owns expense
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, '✏️ Expense updated successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'tracker/edit_expense.html', {'form': form, 'expense': expense})


@login_required
def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk, user=request.user)  # Ensure user owns expense
    if request.method == 'POST':
        expense.delete()
        messages.success(request, '🗑️ Expense deleted!')
        return redirect('expense_list')
    return render(request, 'tracker/delete_expense.html', {'expense': expense})


@login_required
def analytics_view(request):
    """Analytics dashboard with charts and statistics"""
    user_expenses = Expense.objects.filter(user=request.user)
    
    # Monthly spending trend (last 6 months)
    six_months_ago = datetime.now() - timedelta(days=180)
    monthly_data = user_expenses.filter(date__gte=six_months_ago).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Category breakdown
    category_data = user_expenses.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    # Top 5 expenses
    top_expenses = user_expenses.order_by('-amount')[:5]
    
    # Statistics
    total_spent = user_expenses.aggregate(Sum('amount'))['amount__sum'] or 0
    expense_count = user_expenses.count()
    avg_expense = (total_spent / expense_count) if expense_count > 0 else 0
    
    # Convert QuerySets to JSON-serializable format
    import json
    from decimal import Decimal
    
    # Convert category data
    category_list = []
    for item in category_data:
        category_list.append({
            'category': item['category'],
            'total': float(item['total']) if item['total'] else 0
        })
    
    # Convert monthly data
    monthly_list = []
    for item in monthly_data:
        monthly_list.append({
            'month': item['month'].isoformat() if item['month'] else '',
            'total': float(item['total']) if item['total'] else 0
        })
    
    context = {
        'monthly_data': json.dumps(monthly_list),
        'category_data': json.dumps(category_list),
        'top_expenses': top_expenses,
        'total_spent': total_spent,
        'avg_expense': avg_expense,
        'expense_count': expense_count,
    }
    
    return render(request, 'tracker/analytics.html', context)


@login_required
def budget_view(request):
    """Budget management page with progress tracking"""
    user_budgets = Budget.objects.filter(user=request.user)
    
    # Calculate current month total
    now_date = datetime.now()
    current_month_start = now_date.replace(day=1)
    
    current_month_expenses = Expense.objects.filter(
        user=request.user,
        date__gte=current_month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Prepare budget data with progress
    budget_data = []
    total_budgeted = 0
    
    for budget in user_budgets:
        # Get spent amount for this category this month
        spent = Expense.objects.filter(
            user=request.user,
            category=budget.category,
            date__gte=current_month_start
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Calculate percentage using float conversion to avoid Decimal issues
        percentage = (float(spent) / float(budget.amount) * 100) if budget.amount > 0 else 0
        
        total_budgeted += budget.amount
        
        budget_data.append({
            'budget': budget,
            'spent': spent,
            'remaining': budget.amount - spent,
            'remaining_abs': abs(budget.amount - spent),
            'percentage': min(percentage, 100), # Cap at 100 for bar width
            'percentage_val': percentage, # Raw value for logic
            'status': 'safe' if percentage < 75 else 'warning' if percentage < 90 else 'danger'
        })
        
    context = {
        'budgets': budget_data,
        'current_month_total': current_month_expenses,
        'total_budgeted': total_budgeted,
        'current_month': now_date
    }
    
    return render(request, 'tracker/budget.html', context)


@login_required
def add_budget(request):
    """Add a new monthly budget"""
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.user = request.user
            # Set month to current month (first day)
            budget.month = datetime.now().replace(day=1)
            
            # Check if budget already exists for this category/month
            existing = Budget.objects.filter(
                user=request.user,
                category=budget.category,
                month=budget.month
            ).first()
            
            if existing:
                messages.warning(request, f'Budget for {budget.category} already exists! Edited instead.')
                existing.amount = budget.amount
                existing.save()
            else:
                budget.save()
                messages.success(request, '✅ Budget set successfully!')
            return redirect('budget')
    else:
        form = BudgetForm()
    
    return render(request, 'tracker/budget_form.html', {'form': form, 'title': 'Set New Budget'})


@login_required
def edit_budget(request, pk):
    """Edit an existing budget"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, '✏️ Budget updated successfully!')
            return redirect('budget')
    else:
        form = BudgetForm(instance=budget)
    
    return render(request, 'tracker/budget_form.html', {'form': form, 'title': f'Edit Budget: {budget.category}'})


@login_required
def delete_budget(request, pk):
    """Delete a budget"""
    budget = get_object_or_404(Budget, pk=pk, user=request.user)
    if request.method == 'POST':
        budget.delete()
        messages.success(request, '🗑️ Budget deleted!')
        return redirect('budget')
    return render(request, 'tracker/delete_expense.html', {'expense': budget, 'type': 'Budget'})



