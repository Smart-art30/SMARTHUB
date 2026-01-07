from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import FeeStructure, Invoice, Payment, FeeItem
from students.models import Student
from .forms import FeeItemForm

@login_required
@role_required('schooladmin')
def fee_list(request):
    fees = FeeStructure.objects.filter(school=request.user.school)
    return render(request, 'finance/fee_list.htmls', {'fees':fees})

@login_required
@role_required('schooladmin')
def fee_item_list(request, structure_id):
    fee_structure = get_object_or_404(FeeStructure, id=structure_id)
    fee_items = fee_structure.items.all()

    context ={
        'fee_structure': fee_structure,
        'fee_items': fee_items
    }
    return render(request, 'finance/fee_items_list.html', context)

@login_required
@role_required('schooladmin')
def fee_add(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        amount=request.POST.get('amount')
        FeeStructure.objects.create(
            name=name,
            amount=amount,
            school = request.user.school

        )
        return redirect('fee_list')
    return render(request, 'finance/fee_add.html')

@login_required
@role_required('schooladmin')
def invoice_create(request):
    Students = Student.objects.filter(school=request.user.school)
    fees = FeeStructure.objects.filter(school=request.user.school)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        fee_id = request.POST.get('fee')

        Invoice.objects.create(
            student_id=studemt_id,
            fee_id=fee_id
        )
        return redirect('invoice_list')
    return render(request, 'finance/invoice_create.html',{
    'students': students,
    'fees': fees
})

@login_required
def invoice_list(request):
    invoices = Invoice.objects.filter(student__school=request.user.school)
    return render(request, 'finance/invoice_list.html', {'invoives': invoices})

@login_required
@role_required('schooladmin')
def payment_add(request, invoice_id):
    invoice = Invoice.objects.get(id=invoice_id)

    if request.method== 'POST':
        amount  = request.POST.get('amount')
        method =  request.POST.get('method')

        Payment.objects.create(
            invoice=invoice,
            amount=amount,
            method=method
        )
        invoice.is_paid = True
        invoice.save()

        return redirect('invoice_list')
    return render(request, 'finance/payment_add.html', {'invoice': invoice})


def add_fee_item(request, structure_id):
    fee_structure= get_object_or_404(FeeStructure, id=sturucture_id)

    if request.method == 'POST':
        form = FeeItemForm(request.POST)
        if form.is_valid:
            fee_item= form.save(commit=false)
            fee_item.fee_structure=fee_structure
            fee_item.save()
            return redirect('fee_items_list',structure_id=structure_id )
    else:
        form = FeeItemForm()

    context= {
        'form': form,
        'fee_structure': fee_structure
    }
    return render(request, 'finance/add_fee_item.html', context)
