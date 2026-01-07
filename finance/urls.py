from django.urls import path
from . import views

urlpatterns =[
    path('fees/', views.fee_list, name='fee_list'),
    path('fees/add/', views.fee_add, name='fee_add'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/add/',views.invoice_create, name='invoice_create'),
    path('payment/<int:invoice_id>/', views.payment_add, name='payment_add'),
    path('fee-structure/<int:structure_id>/items', views.fee_item_list, name='fee_items_list'),
    path('fee-structure/<int:structure_id>/items/add/', views.add_fee_item, name='add_fee_item'),
]