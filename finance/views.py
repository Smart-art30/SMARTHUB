from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum

from accounts.decorators import role_required
from schools.models import SchoolClass
from students.models import Student

from .models import FeeStructure, FeeItem, Invoice, Payment
from .forms import FeeItemForm




@login_required
@role_required('schooladmin')
def fee_list(request):
    fees = FeeStructure.objects.filter(
        school=request.user.school
    ).order_by('-year', 'term')

    return render(request, 'finance/fee_list.html', {'fees': fees})


@login_required
@role_required('schooladmin')
def fee_item_list(request, structure_id):
    fee_structure = get_object_or_404(
        FeeStructure,
        id=structure_id,
        school=request.user.school
    )

    return render(
        request,
        'finance/fee_items_list.html',
        {'fee_structure': fee_structure}
    )


@login_required
@role_required('schooladmin')
def fee_add(request):
    school = request.user.school
    classes = SchoolClass.objects.filter(school=school)

    if request.method == 'POST':
        student_class = get_object_or_404(
            SchoolClass,
            id=request.POST.get('student_class'),
            school=school
        )

        fee_structure, created = FeeStructure.objects.get_or_create(
            school=school,
            student_class=student_class,
            term=request.POST.get('term'),
            year=request.POST.get('year'),
        )

        if not created:
            messages.error(request, 'Fee structure already exists')
            return redirect('fee_list')

        messages.success(request, 'Fee structure created successfully')
        return redirect('fee_items_list', fee_structure.id)

    return render(request, 'finance/fee_add.html', {'classes': classes})



@login_required
@role_required('schooladmin')
def invoice_create(request):
    students = Student.objects.filter(school=request.user.school)
    fees = FeeStructure.objects.filter(school=request.user.school, is_active=True)

    if request.method == 'POST':
        student = get_object_or_404(
            Student,
            id=request.POST.get('student'),
            school=request.user.school
        )

        fee_structure = get_object_or_404(
            FeeStructure,
            id=request.POST.get('fee'),
            school=request.user.school
        )

        Invoice.objects.create(
            student=student,
            fee_structure=fee_structure,
            total_amount=fee_structure.total_amount
        )

        messages.success(request, 'Invoice created successfully')
        return redirect('invoice_list')

    return render(
        request,
        'finance/invoice_create.html',
        {'students': students, 'fees': fees}
    )


@login_required
@role_required('schooladmin')
def invoice_list(request):
    invoices = Invoice.objects.filter(
        student__school=request.user.school
    ).annotate(
        total_paid=Sum('payments__amount', filter=models.Q(payments__status='confirmed'))
    )

    for invoice in invoices:
        invoice.total_paid = invoice.total_paid or 0
        invoice.balance = invoice.total_amount - invoice.total_paid

    return render(
        request,
        'finance/invoice_list.html',
        {'invoices': invoices}
    )

@login_required
@role_required('schooladmin')
def payment_add(request):
    students = Student.objects.filter(school=request.user.school)
    invoices = Invoice.objects.filter(
        student__school=request.user.school,
        is_paid=False
    )

    if request.method == 'POST':
        invoice = get_object_or_404(
            Invoice,
            id=request.POST.get('invoice'),
            student__school=request.user.school
        )

        Payment.objects.create(
            invoice=invoice,
            amount=request.POST.get('amount'),
            payment_method=request.POST.get('method'),
            settlement_account=request.POST.get('method'),
            transaction_reference=request.POST.get('transaction_reference'),
            status='confirmed'  # cash/manual confirmation
        )

        messages.success(request, 'Payment recorded successfully')
        return redirect('payment_list')

    return render(
        request,
        'finance/payment_add.html',
        {'students': students, 'invoices': invoices}
    )



@login_required
@role_required('schooladmin')
def add_fee_item(request, structure_id):
    fee_structure = get_object_or_404(
        FeeStructure,
        id=structure_id,
        school=request.user.school
    )

    if request.method == 'POST':
        form = FeeItemForm(request.POST)
        if form.is_valid():
            fee_item = form.save(commit=False)
            fee_item.fee_structure = fee_structure
            fee_item.save()
            messages.success(request, 'Fee item added successfully')
            return redirect('fee_items_list', structure_id=structure_id)
    else:
        form = FeeItemForm()

    return render(
        request,
        'finance/add_fee_item.html',
        {'form': form, 'fee_structure': fee_structure}
    )

@login_required
@role_required('schooladmin')
def payment_list(request):
    payments = Payment.objects.filter(
        invoice__student__school=request.user.school
    ).order_by('-payment_date')

    return render(
        request,
        'finance/payment_list.html',
        {'payments': payments}
    )
