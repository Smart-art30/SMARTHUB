from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model
from .forms import SchoolSignupForm
from .models import SubscriptionPLan, SchoolClass
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required


User = get_user_model()

def school_signup(request):
    if request.method == 'POST':
        form = SchoolSignupForm(request.POST)
        if form.is_valid():
            school = form.save(commit=False)
            school.subscription=SubscriptionPLan.objects.first()
            school.save()

            admin = User.objects.create_user(
                username = form.cleaned_data['admin_email'],
                email = form.cleaned_data['admin_email'],
                password = form.cleaned_data['admin_password'],
                role = 'schooladmin',
                school=school
            )
            return redirect('login')
    else:
        form = SchoolSignupForm()
    return render(request, 'schools/sighup.html',{'form': form})
        

@login_required
@role_required('schooladmin')
def class_list(request):
    classes = SchoolClass.objects.filter(school=request.user.school)
    return render(request, 'schools/class_list', {'classes': classes})

@login_required
@role_required('schooladmin')
def class_add(request):
    if request.method=='POST':
        name = request.POST.get('name')
        SchoolClass.objects.create(name=name, school=request.user.school)
        return redirect('class_list')
    return render(request, 'schools/class_add.html')