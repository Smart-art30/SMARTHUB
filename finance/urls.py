from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Fees
    path('fees/', views.fee_list, name='fee_list'),
    path('fees/add/', views.fee_add, name='fee_add'),

    # Fee structure items
    path(
        'fee-structure/<int:structure_id>/items/',
        views.fee_item_list,
        name='fee_items_list'
    ),
    path(
        'fee-structure/<int:structure_id>/items/add/',
        views.add_fee_item,
        name='add_fee_item'
    ),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/add/', views.invoice_create, name='invoice_create'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('school-payment-methods/', views.school_payment_methods, name='school_payment_methods'),
    path('payments/add/<int:invoice_id>/', views.payment_add, name='payment_add'),
    path('payments/add/', views.payment_add, name='payment_add'),

        # FeeStructure edit/delete
    path('fees/<int:fee_id>/edit/', views.fee_edit, name='fee_edit'),
    path('fees/<int:fee_id>/delete/', views.fee_delete, name='fee_delete'),

    # FeeItem edit/delete
    path('fee-structure/<int:structure_id>/items/<int:item_id>/edit/', views.fee_item_edit, name='fee_item_edit'),
    path('fee-structure/<int:structure_id>/items/<int:item_id>/delete/', views.fee_item_delete, name='fee_item_delete'),
    path('fees/<int:fee_id>/print/', views.fee_structure_print, name='fee_structure_print'),
    path('fees/<int:fee_id>/pdf/', views.fee_structure_pdf, name='fee_structure_pdf'),


    path('school-payment-methods/', views.school_payment_methods, name='school_payment_methods'),
    path('school-payment-methods/add/', views.add_payment_method, name='add_payment_method'),
    path('school-payment-methods/<int:pk>/edit/', views.edit_payment_method, name='edit_payment_method'),
    path('school-payment-methods/<int:pk>/delete/', views.delete_payment_method, name='delete_payment_method'),



]

