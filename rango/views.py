from django.shortcuts import render, render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from rango.models import Category, Page, UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.bing_search import run_query

from datetime import datetime

def index(request):
    context = RequestContext(request)

    category_list = Category.objects.order_by('-likes')[:5]
    page_list = Page.objects.order_by('-views')[:5]
    cat_list = get_category_list()
    context_dict = {'categories': category_list,
                    'pages': page_list,
                    'cat_list': cat_list,
                    }

    for category in category_list:
        category.url = encode_url(category.name)

    if request.session.get('last_visit'):
        last_visit_time = request.session.get('last_visit')
        visits = request.session.get('visits', 0)

        if (datetime.now() - datetime.strptime(last_visit_time[:-7], "%Y-%m-%d %H:%M:%S")).seconds > 0:
            request.session['visits'] = visits + 1
            request.session['last_visit'] = str(datetime.now())

    else:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = 1

    return render_to_response('rango/index.html', context_dict, context)

def about(request):
    if request.session.get('visits'):
        count = request.session.get('visits')
    else:
        count = 0

    return render_to_response('rango/about.html', {'visits': count}, RequestContext(request))

def category(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)
    category_valid = get_object_or_404(Category, name=category_name)
    cat_list = get_category_list()
    context_dict = {'category_name_url': category_name_url,
                    'category': category_name,
                    'category_valid': category_valid,
                    'cat_list': cat_list,
                    }
    try:
        category = Category.objects.get(name=category_name)
        pages = Page.objects.filter(category=category)
        context_dict['pages'] = pages
        context_dict['category'] = category

    except Category.DoesNotExist:
        pass

    if request.method == "POST":
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)
            context_dict['result_list'] = result_list
            return render_to_response('rango/category.html', context_dict, context)

    return render_to_response('rango/category.html', context_dict, context)

def add_category(request):
    context = RequestContext(request)

    cat_list = get_category_list()
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            return render_to_response('rango/add_category.html', {'form': form, 'cat_list': cat_list}, context)
    else:
        form = CategoryForm()

    return render_to_response("rango/add_category.html", {'form': form, 'cat_list': cat_list}, context)

def add_page(request, category_name_url):
    context = RequestContext(request)

    category_name = decode_url(category_name_url)
    category_valid = get_object_or_404(Category, name=category_name)

    cat_list = get_category_list()

    if request.method =="POST":
        form = PageForm(request.POST)

        if form.is_valid:
            page = form.save(commit = False)

            try:
                cat = Category.objects.get(name=category_name)
                page.category = cat

            except Category.DoesNotExist:
                return render_to_response('rango/add_page.html', {'form': form, 'cat_list': cat_list}, context)

            page.views = 0

            page.save()
            return category(request, category_name_url)
        else:
            return render_to_response('rango/add_page.html', 
                {'category_name_url': category_name_url,
                 'category_valid': category_valid,
                 'cat_list': cat_list,
                 'form': form}, 
                context)
    else:
        form = PageForm()

    return render_to_response('rango/add_page.html', 
            {'category_name_url': category_name_url,
             'cat_list': cat_list,
             'form': form}, 
            context)

def register(request):
    context = RequestContext(request)
    registered = False
    cat_list = get_category_list()

    if request.method == "POST":
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True

            # need to authenticate user and redirect to homepage with user logged in

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response('rango/register.html',
        {'user_form': user_form, 
         'profile_form':profile_form,
         'cat_list': cat_list,
         'registered': registered,},
         context)

def user_login(request):
    context = RequestContext(request)
    cat_list = get_category_list()

    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                return HttpResponse("Your account is disabled")
        else:
            errors = True
            return render_to_response('rango/login.html',{'errors':errors, 'cat_list': cat_list}, context)
    else:
        return render_to_response('rango/login.html', {'cat_list': cat_list}, context)

def search(request):
    context = RequestContext(request)
    result_list = []
    cat_list = get_category_list()

    if request.method == "POST":
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)

    return render_to_response('rango/search.html', {'result_list': result_list, 'cat_list': get_category_list}, context)

@login_required
def profile(request):
    context = RequestContext(request)
    user_name = request.user
    user_website = request.user.profile.website
    user_picture = request.user.profile.picture
    cat_list = get_category_list()

    return render_to_response('rango/profile.html', {
                                                    "user_name": user_name,
                                                    "user_website": user_website,
                                                    "user_picture": user_picture,
                                                    "cat_list": cat_list,
                                                    }, 
                                                    context)

@login_required
def restricted(request):
    return render_to_response("rango/restricted.html", RequestContext(request))

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')

def get_category_list():
    category_list = Category.objects.all().order_by('name')
    for category in category_list:
        category.url = encode_url(category.name)
    return category_list

def decode_url(category_name):
    return category_name.replace("_", " ")

def encode_url(category_name_url):
    return category_name_url.replace(" ", "_")