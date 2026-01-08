from django.db import models

       
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length= 50)
    max_students = models.PositiveIntegerField()
    max_teachers = models.PositiveIntegerField()
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length= 50, unique = True)
    address = models.TextField(blank =  True, null = True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.ImageField(upload_to='school_logos/',blank=True, null = True)
    created_at = models.DateTimeField(auto_now_add = True)
    subscription = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    subscription_active =models.BooleanField(default=True)
    def __str__(self):
        return self.name

class SchoolClass(models.Model):
    school = models.ForeignKey(School, on_delete = models.CASCADE)
    name = models.CharField(max_length = 50)
    stream  =  models.CharField(max_length=100)
    section = models.CharField(max_length = 10, blank = True, null = True)
    created_at= models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}{self.section} {self.stream} ({self.school.name})'
 