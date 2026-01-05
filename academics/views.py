from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from accounts.decorators import  role_required
from .models import Subject

@login_required
@role_required('schooladmin')
def subject_list(request):
    aubjects = Subject.objects.filter(school=request.user.school)
    return render(request, 'academics/subjects_list.html', {'subjects':subjects})

@login_required
@role_required('schooladmin')
def subject_add(request):
    if request.method =='POST':
        name=request.POST.get('name')
        code = request.POST.get('code')
        Subject.objects.create(name=name, code=code, school=request.user.school)
        return redirect('subject_list')
    return render(request, 'academics/subjects_add.html')
