from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# =========================
# FEE STRUCTURE
# =========================

class FeeStructure(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    student_class = models.ForeignKey('schools.SchoolClass', on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    year = models.IntegerField()

    # Cached total (authoritative)
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('school', 'student_class', 'term', 'year')

    def __str__(self):
        return f'{self.student_class} - {self.term} {self.year}'

    def update_total(self):
        """
        Recalculate and lock fee structure total
        """
        self.total_amount = sum(
            item.amount for item in self.items.all()
        )
        self.save(update_fields=['total_amount'])

    def can_edit(self):
        """
        Fee structure becomes immutable once invoices exist
        """
        return not self.invoice_set.exists()


# =========================
# FEE ITEMS
# =========================

class FeeItem(models.Model):
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT,
        related_name='items'
    )

    name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Fee amount must be greater than zero")

        if not self.fee_structure.can_edit():
            raise ValidationError(
                "Cannot modify fee items after invoices have been issued."
            )

    def delete(self, *args, **kwargs):
        if not self.fee_structure.can_edit():
            raise ValidationError(
                "Cannot delete fee items after invoices have been issued."
            )
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.name} - {self.amount}'


# =========================
# INVOICE
# =========================

class Invoice(models.Model):
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE
    )

    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT
    )

    issued_date = models.DateTimeField(auto_now_add=True)

    # 🔒 Frozen snapshot of total
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    is_paid = models.BooleanField(default=False)

    def total_paid(self):
        return sum(
            payment.amount
            for payment in self.payments.filter(status='confirmed')
        )

    def balance(self):
        return self.total_amount - self.total_paid()

    def credit(self):
        """
        Overpayment credit (if any)
        """
        balance = self.balance()
        return abs(balance) if balance < 0 else 0

    def update_payment_status(self):
        """
        Automatically sync is_paid with balance
        """
        self.is_paid = self.balance() <= 0
        self.save(update_fields=['is_paid'])

    def __str__(self):
        return f'Invoice - {self.student}'


# =========================
# PAYMENT
# =========================

class Payment(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_method = models.CharField(
        max_length=20,
        choices=(
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('mpesa', 'Mpesa'),
        )
    )

    settlement_account = models.CharField(
        max_length=20,
        choices=(
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('mpesa', 'Mpesa'),
        )
    )

    transaction_reference = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('failed', 'Failed'),
        ),
        default='pending'
    )

    payment_date = models.DateTimeField(auto_now_add=True)

    raw_response = models.JSONField(blank=True, null=True)

    def delete(self, *args, **kwargs):
        raise ValidationError("Payments cannot be deleted.")

    def __str__(self):
        return f'{self.amount} - {self.payment_method}'


# =========================
# SIGNALS
# =========================

@receiver([post_save, post_delete], sender=FeeItem)
def update_fee_structure_total(sender, instance, **kwargs):
    instance.fee_structure.update_total()


@receiver(post_save, sender=Payment)
def auto_update_invoice(sender, instance, **kwargs):
    if instance.status == 'confirmed':
        instance.invoice.update_payment_status()
