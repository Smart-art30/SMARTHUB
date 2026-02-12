from django.contrib import admin
from .models import School, SchoolClass, SubscriptionPlan
from finance.models import SchoolPaymentMethod

# =========================
# SCHOOL PAYMENT METHOD INLINE
# =========================
class SchoolPaymentMethodInline(admin.TabularInline):
    model = SchoolPaymentMethod
    extra = 1
    min_num = 1
    verbose_name = "Payment Method"
    verbose_name_plural = "Payment Methods"
    fields = ('method', 'details', 'notes')

# =========================
# SCHOOL PAYMENT METHOD ADMIN
# =========================
@admin.register(SchoolPaymentMethod)
class SchoolPaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('school', 'method', 'details', 'notes')
    list_filter = ('method',)
    search_fields = ('details', 'notes')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Superusers see all, school admins only see their own
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'school'):
            return qs.filter(school=request.user.school)
        return qs.none()

    def save_model(self, request, obj, form, change):
        # Assign the school automatically for non-superusers
        if not request.user.is_superuser and hasattr(request.user, 'school'):
            obj.school = request.user.school
        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Remove school field for school admins
        if not request.user.is_superuser:
            form.base_fields.pop('school', None)
        return form

# =========================
# SCHOOL ADMIN
# =========================
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone', 'email', 'subscription_active')
    search_fields = ('name', 'code', 'email', 'phone')
    inlines = [SchoolPaymentMethodInline]

# =========================
# SCHOOL CLASS ADMIN
# =========================
@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'section','stream', 'school')
    list_filter  = ('school',)
    search_fields = ('name', 'stream', 'section')

    def save_model(self, request, obj, form, change):
        if hasattr(request.user, 'school'):
            obj.school = request.user.school
        super().save_model(request, obj, form, change)

# =========================
# SUBSCRIPTION PLAN ADMIN
# =========================
admin.site.register(SubscriptionPlan)
