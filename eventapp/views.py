from django.shortcuts import render, redirect
from django.forms import modelformset_factory
from django.core.files.storage import FileSystemStorage
from accountapp.models import About
from django.http import Http404, JsonResponse

from django.contrib import messages
from .models import *
import json

from eventapp import models
from django.http import HttpResponseRedirect, HttpResponse
from .forms import ImageForm, PostForm, Personimageform
from django.contrib.auth.decorators import login_required
import os
from django.conf import settings
from django.templatetags.static import static
from django.views import generic

# Create your views here.

def index(request):
    events = models.Postevent.objects.order_by("-created_date")
    images=[]
    for event in events:
        event.images=models.Images.objects.all().order_by("-id")
    
      
    return render(request, "gallery.html", {"events": events})


@login_required
def post(request):

    ImageFormSet = modelformset_factory(models.Images, form=ImageForm, extra=10)
    #'extra' means the number of photos that you can upload   ^
    if request.method == "POST":
        postForm = PostForm(request.POST)
        formset = ImageFormSet(
            request.POST, request.FILES, queryset=models.Images.objects.none()
        )

        if postForm.is_valid() and formset.is_valid():
            post_form = postForm.save(commit=False)
            post_form.user = request.user
            post_form.save()
            id = str(post_form.id)
            for form in formset.cleaned_data:
                # this helps to not crash if the user
                # do not upload all the photos
                if form:
                    image = form["image"]
                    photo = models.Images(post=post_form, image=image)
                    photo.save()
            messages.success(request, "Go to homepage to see changes")
            return redirect("/admin_page/")
        else:
            print(postForm.errors, formset.errors)
    else:
        postForm = PostForm()
        formset = ImageFormSet(queryset=models.Images.objects.none())
    return render(
        request, "gallery/eventbase.html", {"postForm": postForm, "formset": formset}
    )


def memberimage(request):
    if request.method == "POST":
        form = Personimageform(request.POST, request.FILES)
        if form.is_valid():
            imagestored = models.People()
            imagestored.image = form.cleaned_data["personimage"]
            imagestored.save()
    else:
        form = Personimageform()

    return render(request, "postimage.html", locals())


def homePage(request):
    try:
        about = About.objects.all().order_by("-id")[0]
    except:
        about=About()
        about.body="This is about page"
        
    videos = models.Videos.objects.all().order_by("-id")[
            :3
        ]
    people = People.objects.all()
    upcoming_events = models.Postevent.objects.filter(completed=False).order_by(
        "-created_date"
    )[:4]
    for event in upcoming_events:
        event.images = models.Images.objects.filter(post=event)[:1]
        try:
            memberobjs = models.Members.objects.filter(post=event)
            for memberobj in memberobjs:
                event.person = models.People.objects.get(id=memberobj.person.id)
        except:
            pass
    completed_events = models.Postevent.objects.filter(completed=True).order_by(
        "-created_date"
    )[:4]
    for event in completed_events:
        event.images = models.Images.objects.filter(post=event)[:1]
        try:
            memberobjs = models.Members.objects.filter(post=event)
            for memberobj in memberobjs:
                event.person = models.People.objects.get(id=memberobj.person.id)
        except:
            pass
    return render(
        request,
        "home.html",
        {
            "team": people,
            "upcoming_events": upcoming_events,
            "completed_events": completed_events,
            "videos":videos,
            "about":about
        },
    )


def showGallery(request):
    posts = models.Postevent.objects.filter().order_by("-created_date")
    for i in posts:
        i.images = models.Images.objects.filter(post=i)[:2]
    return render(request, "footer.html", {"posts": posts})


def event_detail(request, id):
    eventdetail = models.Postevent.objects.get(id=id)
    eventdetail.images = models.Images.objects.filter(post=eventdetail)

    return render(request, "event_detail.html", {"event": eventdetail})


def upcoming_events(request):
    more=False
    ids = []
    events = models.Postevent.objects.filter(completed=False).order_by("-created_date")[
        :10
    ]
    count = events.count()
    if count == 10:
        more = True
    for i in events:
        ids.append(i.id)
        i.reduceddescription = i.description[:100]
        i.images = models.Images.objects.filter(post=i)
    if(len(ids)):
        ids.sort()
        smallest_id = ids[0]
    else:
        smallest_id = 0
    return render(
        request,
        "events.html",
        {"events": events, "smallest_id": smallest_id, "completed": "u", "more": more},
    )

def completed_events(request):
    more=False
    ids = []
    events = models.Postevent.objects.filter(completed=True).order_by("-created_date")[
        :10
    ]
    count = events.count()
    if count == 10:
        more = True
    for i in events:
        ids.append(i.id)
        i.reduceddescription = i.description[:100]
        i.images = models.Images.objects.filter(post=i)
    if(len(ids)):
        ids.sort()
        smallest_id = ids[0]
    else:
        smallest_id = 0
    return render(
        request,
        "events.html",
        {"events": events, "smallest_id": smallest_id, "completed": "c", "more": more},
    )


def more_events(request, c, id):
    ids = []
    more = False
    if c == "c":
        try:
            events = (
                Postevent.objects.filter(id__lte=id)
                .filter(completed=True)
                .order_by("-created_date")[:10]
            )
            count = events.count()
            if count == 10:
                more = True
            for i in events:
                ids.append(i.id)
                i.reduceddescription = i.description[:100]
                i.images = models.Images.objects.filter(post=i)
            if(len(ids)):
                ids.sort()
                smallest_id = ids[0]
            else:
                smallest_id = 0
        except:
            events = []

        return render(
            request,
            "events.html",
            {
                "events": events,
                "smallest_id": smallest_id,
                "completed": "c",
                "more": more,
            },
        )
    elif c == "u":

        events = (
            Postevent.objects.filter(id__lte=id)
            .filter(completed=False)
            .order_by("-created_date")[:10]
        )
        count = events.count()
        if count == 10:
            more = True

        for i in events:
            ids.append(i.id)
            i.reduceddescription = i.description[:100]
            i.images = models.Images.objects.filter(post=i)
        if(len(ids)):
                ids.sort()
                smallest_id = ids[0]
        else:
            smallest_id = 0
        return render(
            request,
            "events.html",
            {
                "events": events,
                "smallest_id": smallest_id,
                "completed": "c",
                "more": more,
            },
        )
    else:
        return redirect("/")


@login_required
def deletepost(request, id):
    deleted = models.Postevent.objects.get(id=id)
    deleted.delete()
    return redirect("/")
def videos(request):
    if request.method=="GET":
        more=False
        ids = []
        videos = models.Videos.objects.all().order_by("-id")[
            :10
        ]
        count = videos.count()
        if count == 10:
            more = True
        
        if(len(ids)):
            ids.sort()
            smallest_id = ids[0]
        else:
            smallest_id = 0
        return render(
            request,
            "videos.html",
            {"videos": videos, "smallest_id": smallest_id, "more": more}
        )
    elif request.method=="POST":
        title=request.POST["video_title"]
        url=request.POST["video_url"]
        video=models.Videos()
        if(title):
            video.title=title
            if(url):
                link_id=[]
                index=0
                for i in url:
                    index+=1
                    if (i == '='):
                        link_id=url[index:len(url)]
                        video.url=link_id
                        video.save()
                        break
                        
                return redirect("/")
                    
                
        else:
            return HttpResponse("There was an error.. Try again!!!")
        return redirect("/")

@login_required
def add_members(request, id):
    people = models.People.objects.all()
    try:
        event = models.Postevent.objects.get(id=id)
        for person in people:
            try:
                member = models.Members.objects.filter(event=event).get(person=person)
                if member:  
                    person.truth = True
            except:
                person.truth = False
    except:
        return redirect("/")
    return render(request, "gallery/add_members.html", {"people": people, "pid": id})


@login_required
def add_member(request, pid, mid):
    if request.method == "POST":
        try:
            event = models.Postevent.objects.get(id=pid)
            try:
                person = models.People.objects.get(id=mid)
                try:

                    member = models.Members.objects.filter(person=person).get(
                        event=event
                    )
                    if member:
                        member.delete()
                        truth = "false"
                        return JsonResponse({"data": truth})
                except:

                    nmember = models.Members()
                    nmember.person = person
                    nmember.event = event
                    nmember.save()

                    return JsonResponse({"data": "true"})
            except:
                return redirect("/")
        except:
            return redirect("/")

