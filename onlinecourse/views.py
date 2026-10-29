from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Course, Lesson, Question, Choice, Submission, Enrollment


class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        return Course.objects.order_by('-total_enrollment')[:10]


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_details_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    if user.is_authenticated:
        Enrollment.objects.get_or_create(user=user, course=course)
        course.total_enrollment += 1
        course.save()
    return redirect('onlinecourse:course_details', pk=course.id)


# Task 5: submit view
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user
    
    if request.method == 'POST':
        enrollment = Enrollment.objects.filter(user=user, course=course).first()
        if not enrollment:
            enrollment = Enrollment.objects.create(user=user, course=course, mode='honor')

        submission = Submission.objects.create(enrollment=enrollment)
        
        # Collect selected choices from POST request
        selected_ids = []
        for key, value in request.POST.items():
            if key.startswith('choice_'):
                selected_ids.append(int(value))

        for choice_id in selected_ids:
            choice = Choice.objects.get(id=choice_id)
            submission.choices.add(choice)

        submission.save()
        return HttpResponseRedirect(reverse('onlinecourse:show_exam_result', args=(course.id, submission.id)))
    
    return redirect('onlinecourse:course_details', pk=course.id)


# Task 5: show_exam_result view
def show_exam_result(request, course_id, submission_id):
    context = {}
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    selected_choices = submission.choices.all()
    selected_ids = [c.id for c in selected_choices]
    
    total_score = 0
    total_possible = 0
    questions = course.question_set.all()
    
    for question in questions:
        total_possible += question.grade
        if question.is_get_score(selected_ids):
            total_score += question.grade

    context['course'] = course
    context['submission'] = submission
    context['grade'] = total_score
    context['total_score'] = total_score
    context['total_possible'] = total_possible if total_possible > 0 else 100
    context['is_passed'] = total_score >= (total_possible * 0.7) if total_possible > 0 else True
    
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)


def login_request(request):
    if request.method == 'POST':
        username = request.POST['username']
        psw = request.POST['psw']
        user = authenticate(username=username, password=psw)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
    return render(request, 'onlinecourse/user_login.html')


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def registration_request(request):
    if request.method == 'POST':
        username = request.POST['username']
        psw = request.POST['psw']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        user = User.objects.create_user(username=username, password=psw, first_name=first_name, last_name=last_name)
        login(request, user)
        return redirect('onlinecourse:index')
    return render(request, 'onlinecourse/user_registration.html')
