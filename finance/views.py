from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .models import FeeStructure, Invoice, Payment, FeeItem
from students.models import Student
from .forms import FeeItemForm
from django.db.models import Sum
from schools.models import SchoolClass


@login_required
@role_required('schooladmin')
def fee_list(request):
    fees = FeeStructure.objects.filter(school=request.user.school)
    return render(request, 'finance/fee_list.html', {'fees':fees})

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
        amount = request.POST.get('amount')

      
        fee = FeeStructure.objects.create(
            name=name,
            amount=amount,
            school=request.user.school
        )

        
        students = Student.objects.filter(school=request.user.school)
        for student in students:
            Invoice.objects.create(
                student=student,
                fee=fee,
            )

        return redirect('fee_list')

    return render(request, 'finance/fee_add.html')

@login_required
@role_required('schooladmin')
def invoice_create(request):
    Students = student.objects.filter(school=request.user.school)
    fees = FeeStructure.objects.filter(school=request.user.school)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        fee_id = request.POST.get('fee')

        Invoice.objects.create(
            student_id=student_id,
            fee_id=fee_id
        )
        return redirect('invoice_list')
    return render(request, 'finance/invoice_create.html',{
    'students': students,
    'fees': fees
})


def invoice_list(request):
    invoices = Invoice.objects.all().annotate(
        total_paid=Sum('payments__amount')
    )

    
    for invoice in invoices:
        invoice.total_paid = invoice.total_paid or 0
        invoice.balance = invoice.fee.amount - invoice.total_paid

    context = {
        'invoices': invoices
    }
    return render(request, 'finance/invoice_list.html', context)
    
@login_required
@role_required('schooladmin')
def payment_add(request):
    """
    Admin adds a payment:
    - Classes filtered by logged-in school
    - Students and invoices filtered dynamically
    """
    classes = SchoolClass.objects.filter(school=request.user.school)
  
    students = Student.objects.filter(school=request.user.school)
    invoices = Invoice.objects.filter(student__school=request.user.school, is_paid=False)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        invoice_id = request.POST.get('invoice')
        amount = float(request.POST.get('amount'))
        payment_method = request.POST.get('method')
        transaction_reference = request.POST.get('transaction_reference', '')

        invoice = get_object_or_404(Invoice, id=invoice_id)

        
        total_paid = invoice.payments.aggregate(total=Sum('amount'))['total'] or 0
        if total_paid + amount > invoice.fee.amount:
            error = f"Cannot pay more than balance: {invoice.fee.amount - total_paid:.2f}"
            return render(request, 'finance/payment_add.html', {
                'classes': classes,
                'students': students,
                'invoices': invoices,
                'error': error
            })

       
        Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference
        )

        total_paid += amount
        if total_paid >= invoice.fee.amount:
            invoice.is_paid = True
            invoice.save()

        return redirect('payment_list')

    return render(request, 'finance/payment_add.html', {
        'classes': classes,
        'students': students,
        'invoices': invoices
    })



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

@login_required
@role_required('schooladmin')
def payment_list(request):
    """
    Display all payments for students in the logged-in admin's school.
    """
    payments = Payment.objects.filter(invoice__student__school=request.user.school)
    return render(request, 'finance/payment_list.html', {'payments': payments})
