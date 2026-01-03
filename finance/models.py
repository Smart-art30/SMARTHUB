from django.db import models
from schools.models import School, SchoolClass


class FeeStructure(models.Model):
    school = models.ForeignKey('schools.School', on_delete=models.CASCADE)
    student_class = models.ForeignKey('schools.SchoolClass', on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    year = models.IntegerField()

    def __str__(self):
        return f'{self.student_class} - {self.term} {self.year}'


class FeeItem(models.Model):
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=100) # Tuition, Lunch, Transport
    amount = models.DecimalField(max_digits =  10, decimal_places = 2)

    def __str__(self):
        return  f'{self.name} - {self.amount}'

class Invoice(models.Model):
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    issued_date = models.DateField(auto_now_add=True)
    is_paid = models.BooleanField(default=False) 

    def total_amount(self):
        return sum(item.amount for item in self.fee_structure.items.all())
    def total_paid(self):
        return sum(payment.amount for payment in self.payments.all())
    def balance(self):
        return self.total_amount() - self.total_paid()
    def __str__(self):
        return f'Invoice - {self.student}'


class Payment(models.Model):
    Invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits= 10, decimal_places=2)
    payment_method = models.CharField(
        max_length =  20,
        choices =(
            ('cash', 'Cash'),
            ('bank', 'Bank'),
            ('mpesa', 'Mpesa'),
        )
    )
    transaction_reference = models.CharField(max_length=100, blank= True, null=True)
    payment_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.amount} - {self.payment_method}'