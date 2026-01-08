from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model
from .forms import SchoolSignupForm
from .models import SubscriptionPlan, SchoolClass
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .forms import SchoolClassForm



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
def add_class(request):
    if request.method == 'POST':
        form = SchoolClassForm(request.POST)
        if form.is_valid():
            school_class = form.save(commit=False)
            school_class.school = request.user.school
            school_class.save()
            return redirect('class_list')
    else:
        form = SchoolClassForm()

    return render(request, 'schools/add_class.html', {'form': form})

@login_required
@role_required('schooladmin')
def edit_class(request, class_id):
    classes = get_object_or_404(SchoolClass, id=class_id, school=request.user.school)
    if request.method == 'POST':
        form = SchoolClassForm(request.POST, instance=classes)
        if form.is_valid():
            form.save()
            return redirect('schooladin_dashborad')
    else:
        form=SchoolClassForm(instance=classes)
    return render(request, 'schools/add_class.html', {'form':form, 'edit':True})

@login_required
@role_required('schooladmin')
def delete_class(request, class_id):
    cls = get_object_or_404(SchoolClass, id=class_id, school=request.user.school)
    if request.method == 'POST':
        cls.delete()
        return redirect('schooladmin_dashboard')
    return render(request, 'schools/confirm_delete.html', {'object': cls})
