from django.contrib import admin
from .models import FeeStructure, FeeItem, Invoice,Payment

admin.site.register(FeeStructure)
admin.site.register(FeeItem)
admin.site.register(Invoice)
admin.site.register(Payment)

