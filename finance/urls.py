from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Fees
    path('fees/', views.fee_list, name='fee_list'),
    path('fees/add/', views.fee_add, name='fee_add'),

    # Invoices
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/add/', views.invoice_create, name='invoice_create'),

    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/<int:invoice_id>/', views.payment_add, name='payment_add'),

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
    path('payments/add/', views.payment_add, name='payment_add'),
    path('payments/add/<int:invoice_id>/', views.payment_add, name='payment_add'),


]
