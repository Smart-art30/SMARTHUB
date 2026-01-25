from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model
from .forms import SchoolSignupForm
from .models import SubscriptionPlan, SchoolClass
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from .forms import SchoolClassForm
from django.shortcuts import get_object_or_404
from django.contrib import messages




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
    return render(request, 'schools/signup.html',{'form': form})
        

@login_required
@role_required('schooladmin')
def class_list(request):
    classes = SchoolClass.objects.filter(school=request.user.school)
    return render(request, 'schools/class_list.html', {'classes': classes})


@login_required
@role_required('schooladmin')
def add_class(request):
    if request.method == 'POST':
        form = SchoolClassForm(request.POST, user=request.user)  
        if form.is_valid():
            school_class = form.save(commit=False)
            school_class.school = request.user.school
            school_class.save()
            form.save_m2m() 
            messages.success(request, f"Class '{school_class}' added successfully.")
            return redirect('schools:class_list')
    else:
        form = SchoolClassForm(user=request.user)  
    return render(request, 'schools/add_class.html', {'form': form})


@login_required
@role_required('schooladmin')
def edit_class(request, class_id):
    cls = get_object_or_404(SchoolClass, id=class_id, school=request.user.school)
    if request.method == 'POST':
        form = SchoolClassForm(request.POST, instance=cls, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Class '{cls}' updated successfully.")
            return redirect('schools:class_list')
    else:
        form = SchoolClassForm(instance=cls, user=request.user)
    return render(request, 'schools/add_class.html', {'form': form, 'edit': True})



@login_required
@role_required('schooladmin')
def delete_class(request, class_id):
    try:
        cls = SchoolClass.objects.get(id=class_id, school=request.user.school)
    except SchoolClass.DoesNotExist:
        messages.error(request, "This class does not exist or you don't have permission to delete it.")
        return redirect('schools:class_list')

    if request.method == 'POST':
        cls.delete()
        messages.success(request, f"Class '{cls.name}' deleted successfully.")
        return redirect('schools:class_list')

    return render(request, 'schools/confirm_delete.html', {'object': cls})