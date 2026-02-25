from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q

from accounts.decorators import role_required
from schools.models import SchoolClass
from students.models import Student

from .models import FeeStructure, FeeItem, Invoice, Payment
from .forms import FeeItemForm
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from finance.models import SchoolPaymentMethod
from .forms import SchoolPaymentMethodForm
from decimal import Decimal
from django.core.exceptions import ValidationError
from .forms import FeeStructureForm
from django.forms import inlineformset_factory
from collections import defaultdict






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
    fee_items = FeeItem.objects.filter(fee_structure=fee_structure)

    return render(
        request,
        'finance/fee_items_list.html',
        {'fee_structure': fee_structure, 'fee_items': fee_items}
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
            return redirect('finance:fee_list')

        messages.success(request, 'Fee structure created successfully. Add fee items now.')
        return redirect('finance:add_fee_item', structure_id=fee_structure.id)

    return render(request, 'finance/fee_add.html', {'classes': classes})

################################################################################################################################
@login_required
@role_required('schooladmin')
def fee_structure_print(request, fee_id):
    fee_structure = get_object_or_404(FeeStructure, id=fee_id, school=request.user.school)
    fee_items = FeeItem.objects.filter(fee_structure=fee_structure)
    total_amount = fee_items.aggregate(total=Sum('amount'))['total'] or 0 

    school = request.user.school

  
    payment_methods = school.payment_methods.all()

    return render(request, 'finance/fee_structure_print.html', {
        'fee_structure': fee_structure,
        'fee_items': fee_items,
        'total_amount': total_amount,
        'school': school,
        'payment_methods': payment_methods,  
    })


#########################################

@login_required
@role_required('schooladmin')
def school_payment_methods(request):
    school = request.user.school  
    methods = SchoolPaymentMethod.objects.filter(school=school)  
    return render(request, "finance/school_payment_methods.html", {"methods": methods})



@login_required
def add_payment_method(request):
    if request.method == 'POST':
        form = SchoolPaymentMethodForm(request.POST)
        if form.is_valid():
            method = form.save(commit=False)
            method.school = request.user.school
            method.save()
            messages.success(request, "Payment method added successfully!")
            return redirect('finance:school_payment_methods')
    else:
        form = SchoolPaymentMethodForm()
    return render(request, "finance/payment_method_form.html", {"form": form, "title": "Add Payment Method"})

@login_required
def edit_payment_method(request, pk):
    method = get_object_or_404(SchoolPaymentMethod, pk=pk, school=request.user.school)
    if request.method == 'POST':
        form = SchoolPaymentMethodForm(request.POST, instance=method)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment method updated successfully!")
            return redirect('finance:school_payment_methods')
    else:
        form = SchoolPaymentMethodForm(instance=method)
    return render(request, "finance/payment_method_form.html", {"form": form, "title": "Edit Payment Method"})

@login_required
def delete_payment_method(request, pk):
    method = get_object_or_404(SchoolPaymentMethod, pk=pk, school=request.user.school)
    if request.method == 'POST':
        method.delete()
        messages.success(request, "Payment method deleted successfully!")
        return redirect('finance:school_payment_methods')
    return render(request, "finance/payment_method_confirm_delete.html", {"method": method})


@login_required
@role_required('schooladmin')
def fee_structure_pdf(request, fee_id):
    fee_structure = get_object_or_404(FeeStructure, id=fee_id, school=request.user.school)
    fee_items = FeeItem.objects.filter(fee_structure=fee_structure)
    school = request.user.school  

    payment_methods = school.payment_methods.all()  

    if school.logo:
        logo_url = request.build_absolute_uri(school.logo.url)
    else:
        logo_url = request.build_absolute_uri(static('images/school_logo.png'))

    html_string = render_to_string('finance/fee_structure_print.html', {
        'fee_structure': fee_structure,
        'fee_items': fee_items,
        'school': school,
        'logo_url': logo_url,
        'payment_methods': payment_methods,  
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))  
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename=FeeStructure_{fee_structure.student_class.name}.pdf'
    return response




##################################################################################################################################################


def fee_edit(request, fee_id):
    fee_structure = get_object_or_404(FeeStructure, pk=fee_id)

  
    FeeItemFormSet = inlineformset_factory(
        FeeStructure,
        FeeItem,
        form=FeeItemForm,
        extra=1,          
        can_delete=True    
    )

    
    if not fee_structure.can_edit():
        messages.warning(request, "This fee structure cannot be edited because some invoices are already paid.")
        return redirect('finance:fee_list')

    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        formset = FeeItemFormSet(request.POST, instance=fee_structure)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Fee structure and items updated successfully.")
            return redirect('finance:fee_list')
    else:
        form = FeeStructureForm(instance=fee_structure)
        formset = FeeItemFormSet(instance=fee_structure)

    return render(request, 'finance/fee_edit.html', {
        'form': form,
        'formset': formset,
        'fee_structure': fee_structure,
    })


@login_required
@role_required('schooladmin')
def fee_delete(request, fee_id):
    fee_structure = get_object_or_404(FeeStructure, id=fee_id, school=request.user.school)

    if not fee_structure.can_edit():
        messages.error(request, "This fee structure cannot be deleted.")
        return redirect('finance:fee_list')

    if request.method == 'POST':
        fee_structure.delete()
        messages.success(request, "Fee structure deleted successfully.")
        return redirect('finance:fee_list')

    return render(request, 'finance/fee_delete.html', {'fee_structure': fee_structure})



@login_required
@role_required('schooladmin')
def fee_item_edit(request, structure_id, item_id):
    fee_structure = get_object_or_404(FeeStructure, id=structure_id, school=request.user.school)
    fee_item = get_object_or_404(FeeItem, id=item_id, fee_structure=fee_structure)

    if not fee_structure.can_edit():
        messages.error(request, "Cannot edit items of this fee structure.")
        return redirect('finance:fee_items_list', structure_id=structure_id)

    if request.method == 'POST':
        form = FeeItemForm(request.POST, instance=fee_item, fee_structure=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee item updated successfully.")
            return redirect('finance:fee_items_list', structure_id=structure_id)
    else:
        form = FeeItemForm(instance=fee_item, fee_structure=fee_structure)

    return render(request, 'finance/add_fee_item.html', {
        'form': form,
        'fee_structure': fee_structure,
        'fee_items': FeeItem.objects.filter(fee_structure=fee_structure)
    })


@login_required
@role_required('schooladmin')
def fee_item_delete(request, structure_id, item_id):
    fee_structure = get_object_or_404(FeeStructure, id=structure_id, school=request.user.school)
    fee_item = get_object_or_404(FeeItem, id=item_id, fee_structure=fee_structure)

    if not fee_structure.can_edit():
        messages.error(request, "Cannot delete items of this fee structure.")
        return redirect('finance:fee_items_list', structure_id=structure_id)

    if request.method == 'POST':
        fee_item.delete()
        messages.success(request, "Fee item deleted successfully.")
        return redirect('finance:fee_items_list', structure_id=structure_id)

    return render(request, 'finance/fee_item_delete.html', {'fee_item': fee_item, 'fee_structure': fee_structure})
#############################################################################################################################
@login_required
@role_required('schooladmin')
def invoice_create(request):
    school = request.user.school

    
    classes = SchoolClass.objects.filter(school=school)

    
    students = Student.objects.filter(school=school)

    
    fees = FeeStructure.objects.filter(school=school, is_active=True)

    if request.method == 'POST':
        student = get_object_or_404(
            Student,
            id=request.POST.get('student'),
            school=school
        )

        fee_structure = get_object_or_404(
            FeeStructure,
            id=request.POST.get('fee'),
            school=school
        )

        Invoice.objects.create(
            student=student,
            fee_structure=fee_structure,
            total_amount=fee_structure.total_amount
        )

        messages.success(request, 'Invoice created successfully.')
        return redirect('finance:invoice_list')

    return render(request, 'finance/invoice_create.html', {
        'classes': classes,
        'students': students,
        'fees': fees,
    })



@login_required
@role_required('schooladmin')
def invoice_list(request):
   
    invoices = Invoice.objects.filter(
        student__school=request.user.school
    ).select_related(
        'student__user',
        'fee_structure__student_class'
    )

    
    for invoice in invoices:
       
        invoice.total_amount_display = invoice.fee_structure.total_amount if not invoice.is_paid else invoice.total_amount

       
        invoice.total_paid = invoice.payments.filter(status='confirmed').aggregate(
            total=Sum('amount')
        )['total'] or 0

        
        invoice.balance = invoice.total_amount_display - invoice.total_paid

  
    invoices_by_class_dict = defaultdict(list)
    for invoice in invoices:
        class_name = invoice.fee_structure.student_class.name
        invoices_by_class_dict[class_name].append(invoice)

    
    invoices_by_class = list(invoices_by_class_dict.items())

    return render(request, 'finance/invoice_list.html', {
        'invoices_by_class': invoices_by_class
    })


@login_required
@role_required('schooladmin')
def payment_add(request, invoice_id=None):
    school = request.user.school

    classes = SchoolClass.objects.filter(school=school)
    students = Student.objects.filter(school=school)
    invoices = Invoice.objects.filter(student__school=school, is_paid=False)

    preselected_invoice_id = invoice_id or request.GET.get('invoice')

    if request.method == 'POST':
        invoice_pk = request.POST.get('invoice') or invoice_id
        invoice = get_object_or_404(
            Invoice,
            id=invoice_pk,
            student__school=school
        )

        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        settlement_account = request.POST.get('settlement_account') or payment_method
        transaction_reference = request.POST.get('transaction_reference') or None

        Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            settlement_account=settlement_account,
            transaction_reference=transaction_reference,
            status='pending'
        )

        messages.success(request, "Payment recorded and awaiting confirmation.")
        return redirect('finance:payment_list')

    return render(request, 'finance/payment_add.html', {
        'classes': classes,
        'students': students,
        'invoices': invoices,
        'preselected_invoice_id': preselected_invoice_id
    })



@login_required
@role_required('schooladmin')
def payment_confirm(request, payment_id):
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        invoice__student__school=request.user.school
    )

    if payment.status != 'pending':
        messages.warning(request, "Only pending payments can be confirmed.")
        return redirect('finance:payment_list')

    payment.status = 'confirmed'
    payment.save()

    
    invoice = payment.invoice

    total_paid = invoice.payments.filter(status='confirmed').aggregate(
        total=Sum('amount')
    )['total'] or 0

    if total_paid >= invoice.total_amount:
        invoice.is_paid = True
        invoice.save()

    messages.success(request, "Payment confirmed successfully.")
    return redirect('finance:payment_list')



@login_required
@role_required('schooladmin')
def payment_fail(request, payment_id):
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        invoice__student__school=request.user.school
    )

    if payment.status != 'pending':
        messages.warning(request, "Only pending payments can be marked failed.")
        return redirect('finance:payment_list')

    payment.status = 'failed'
    payment.save()

    messages.success(request, "Payment marked as failed.")
    return redirect('finance:payment_list')



@login_required
@role_required('schooladmin')
def add_fee_item(request, structure_id):
    fee_structure = get_object_or_404(
        FeeStructure,
        id=structure_id,
        school=request.user.school
    )

    if request.method == 'POST':
        form = FeeItemForm(request.POST, fee_structure=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, 'Fee item added successfully.')
            return redirect('finance:fee_items_list', structure_id=structure_id)
    else:
        form = FeeItemForm(fee_structure=fee_structure)

    fee_items = FeeItem.objects.filter(fee_structure=fee_structure)

    return render(
        request,
        'finance/add_fee_item.html',
        {
            'form': form,
            'fee_structure': fee_structure,
            'fee_items': fee_items
        }
    )




@login_required
@role_required('schooladmin')
def payment_list(request):
    status_filter = request.GET.get('status')

    # Fetch payments for this school, with related student & user to avoid extra queries
    payments = Payment.objects.select_related(
        'invoice',
        'invoice__student',
        'invoice__student__user'
    ).filter(
        invoice__student__school=request.user.school
    )

    if status_filter:
        payments = payments.filter(status=status_filter)

    payments = payments.order_by('-payment_date')

    # Calculate balance for each payment
    for payment in payments:
        total_paid = Payment.objects.filter(
            invoice=payment.invoice,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0

        payment.balance = payment.invoice.total_amount - total_paid

    # Total amount of filtered payments
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0

    return render(
        request,
        'finance/payment_list.html',
        {
            'payments': payments,
            'status_filter': status_filter,
            'total_amount': total_amount
        }
    )


@login_required
@role_required('schooladmin')
def invoice_print(request, invoice_id=None, class_id=None):
    school = request.user.school

    invoices_data = []

    if invoice_id:
        invoice = get_object_or_404(
            Invoice.objects.select_related(
                'student__user',
                'fee_structure__student_class'
            ),
            id=invoice_id,
            student__school=school
        )
        fee_items = FeeItem.objects.filter(fee_structure=invoice.fee_structure)
        total_paid = invoice.payments.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0
        balance = invoice.total_amount - total_paid
        invoices_data.append({
            'invoice': invoice,
            'fee_items': fee_items,
            'total_paid': total_paid,
            'balance': balance
        })

    elif class_id:
        invoices = Invoice.objects.filter(
            student__school=school,
            fee_structure__student_class_id=class_id
        ).select_related(
            'student__user',
            'fee_structure__student_class'
        )
        for invoice in invoices:
            fee_items = FeeItem.objects.filter(fee_structure=invoice.fee_structure)
            total_paid = invoice.payments.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0
            balance = invoice.total_amount - total_paid
            invoices_data.append({
                'invoice': invoice,
                'fee_items': fee_items,
                'total_paid': total_paid,
                'balance': balance
            })

    else:
        return redirect('finance:invoice_list')

    return render(request, 'finance/invoice_print.html', {
        'invoices_data': invoices_data,
        'school': school
    })




def finance_dashboard(request):
    recent_invoices = Invoice.objects.select_related('student', 'fee_structure').order_by('-issued_date')[:20]
    
    total_collected = sum(inv.total_paid() for inv in recent_invoices)
    total_pending = sum(inv.balance() for inv in recent_invoices)
    
    students_paid_count = sum(1 for inv in recent_invoices if inv.is_paid)
    students_pending_count = sum(1 for inv in recent_invoices if not inv.is_paid)

   
    from django.db.models.functions import ExtractMonth
    monthly_data = Invoice.objects.filter(is_paid=True).annotate(month=ExtractMonth('issued_date')) \
                    .values('month').annotate(amount=Sum('total_amount')).order_by('month')

    chart_labels = [entry['month'] for entry in monthly_data]
    chart_data = [float(entry['amount']) for entry in monthly_data]

    context = {
        'recent_invoices': recent_invoices,
        'total_collected': total_collected,
        'total_pending': total_pending,
        'students_paid_count': students_paid_count,
        'students_pending_count': students_pending_count,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'finance/finance_dashboard.html', context)




def student_invoices(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    invoices = Invoice.objects.filter(student=student)
    return render(request, 'finance/student_invoices.html', {
        'student': student,
        'invoices': invoices
    })