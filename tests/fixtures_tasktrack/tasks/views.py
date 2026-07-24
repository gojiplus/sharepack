from django.shortcuts import render, redirect, get_object_or_404
from .models import Task


def task_list(request):
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        priority = int(request.POST.get("priority", 2))
        notes = request.POST.get("notes", "").strip()
        if title:
            Task.objects.create(title=title, priority=priority, notes=notes)
        return redirect("task_list")
    tasks = Task.objects.all()
    open_count = tasks.filter(done=False).count()
    return render(request, "tasks/list.html", {"tasks": tasks, "open_count": open_count})


def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    return render(request, "tasks/detail.html", {"task": task})


def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk)
    task.done = not task.done
    task.save()
    return redirect("task_list")


def task_delete(request, pk):
    Task.objects.filter(pk=pk).delete()
    return redirect("task_list")
