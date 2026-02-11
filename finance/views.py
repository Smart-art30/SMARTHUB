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

    return render(request, 'finance/fee_structure_print.html', {
        'fee_structure': fee_structure,
        'fee_items': fee_items,
        'total_amount': total_amount,
        'school': school,
        'term_start_date': fee_structure.term_start_date,
        'term_end_date': fee_structure.term_end_date,
    })


#########################################


@login_required
@role_required('schooladmin')
def fee_structure_pdf(request, fee_id):
    fee_structure = get_object_or_404(FeeStructure, id=fee_id, school=request.user.school)
    fee_items = FeeItem.objects.filter(fee_structure=fee_structure)
    school = request.user.school  

    html_string = render_to_string('finance/fee_structure_print.html', {
        'fee_structure': fee_structure,
        'fee_items': fee_items,
        'school': school,
        'term_start_date': fee_structure.term_start_date,
        'term_end_date': fee_structure.term_end_date,
    })

    html = HTML(string=html_string)
    pdf = html.write_pdf()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename=FeeStructure_{fee_structure.student_class.name}.pdf'
    return response



##################################################################################################################################################

@login_required
@role_required('schooladmin')
def fee_edit(request, fee_id):
    fee_structure = get_object_or_404(FeeStructure, id=fee_id, school=request.user.school)

    if not fee_structure.can_edit():
        messages.error(request, "This fee structure cannot be edited.")
        return redirect('finance:fee_list')

    if request.method == 'POST':
        form = FeeStructureForm(request.POST, instance=fee_structure)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee structure updated successfully.")
            return redirect('finance:fee_list')
    else:
        form = FeeStructureForm(instance=fee_structure)

    return render(request, 'finance/fee_edit.html', {'form': form, 'fee_structure': fee_structure})


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
        return redirect('finance:invoice_list')

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
        total_paid=Sum('payments__amount', filter=Q(payments__status='confirmed'))

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
            status='confirmed' 
        )

        messages.success(request, 'Payment recorded successfully')
        return redirect('finance:payment_list')

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
    payments = Payment.objects.filter(
        invoice__student__school=request.user.school
    ).order_by('-payment_date')

    return render(
        request,
        'finance/payment_list.html',
        {'payments': payments}
    )
