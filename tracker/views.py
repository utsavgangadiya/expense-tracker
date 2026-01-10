# tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from .models import Expense
from .forms import ExpenseForm
from django.utils.timezone import now 
from datetime import timedelta
from django.template.loader import get_template
from django.http import HttpResponse
from xhtml2pdf import pisa


def expense_list(request):
    expenses = Expense.objects.all()

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

    }

    return render(request, 'tracker/expense_list.html', context)




def export_expenses_pdf(request):
    expenses = Expense.objects.all().order_by('-date')

    template_path = 'tracker/pdf_template.html'
    context = {'expenses': expenses}

    template = get_template(template_path)
    html = template.render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="expenses.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)

    if pisa_status.err:
        return HttpResponse('Error generating PDF')
    return response


def add_expense(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Expense added successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'tracker/add_expense.html', {'form': form})


def edit_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, '✏️ Expense updated successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'tracker/edit_expense.html', {'form': form, 'expense': expense})


def delete_expense(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, '🗑️ Expense deleted!')
        return redirect('expense_list')
    return render(request, 'tracker/delete_expense.html', {'expense': expense})

  
    