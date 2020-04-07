import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
#from django.views.decorators.cache import cache_page
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm


# Убрал лишнии комментарии, оставил только важные

#@cache_page(20)
def index(request):
        post_list = Post.objects.order_by("-pub_date").all()
        paginator = Paginator(post_list, 10)  # показывать по 10 записей на странице.
        page_number = request.GET.get('page')  # переменная в URL с номером запрошенной страницы
        page = paginator.get_page(page_number)  # получить записи с нужным смещением

        return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
        # функция get_object_or_404 позволяет получить объект из базы данных
        # по заданным критериям или вернуть сообщение об ошибке если объект не найден
        group = get_object_or_404(Group, slug=slug)
        posts = Post.objects.filter(group=group).order_by(
                "-pub_date").all()  # filter - аналог WHERE group_id = {group_id}
        paginator = Paginator(posts, 10)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)
        return render(request, "group.html", {"group": group, "posts": posts, 'paginator': paginator, 'page': page})


def new_post(request):
        if request.user.is_authenticated:  # Праверка авторизации
                if request.method == 'POST':
                        form = PostForm(request.POST)
                        
                        if form.is_valid():
                                post=Post.objects.create(author=request.user, text=form.cleaned_data['text'],
                                                     group=form.cleaned_data['group'])
                                form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
                                form.save()
                                
                        # if form.is_valid():
                        #         Post.objects.create(author=request.user, text=form.cleaned_data['text'],
                        #                             group=form.cleaned_data['group'])
                                return redirect('/')
                form = PostForm()
                return render(request, 'new.html', {'form': form})
        return redirect(
                '/')  # Если пользователь не авторизован и пытается войти на стр new то его сразу перенаправляет на главную


def profile(request, username):
        author_profile = User.objects.get(username=username)
        posts = Post.objects.filter(author=author_profile).order_by("-pub_date")
        paginator = Paginator(posts, 10)
        page_number = request.GET.get('page')
        page = paginator.get_page(page_number)
        following = False
        #Follow.objects.filter(user=request.user).exclude(author=author).count() == 0:
        if request.user.is_authenticated:
                following = Follow.objects.filter(user=request.user).filter(author=author_profile)
        return render(request, "profile.html",
                      {"posts": posts, "username": username, "author_profile": author_profile, 'page': page,
                       'paginator': paginator, 'following':following})


def post_view(request, username, post_id):
        #author_profile = User.objects.get(username=username)
        #post = Post.objects.filter(author=author_profile).get(id=post_id)
        author_profile = get_object_or_404(User, username=username)
        post = get_object_or_404(Post, id=post_id)
        number = Post.objects.filter(author=author_profile).count()
        form = CommentForm()
        items = Comment.objects.filter(post=post).order_by("created")
        return render(request, "post.html",
                      {"post": post, "username": username, 
                      "author_profile": author_profile, "number": number, "form": form, "items":items})

@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect("post", username=request.user.username, post_id=post_id)
    # добавим в form свойство files
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username, post_id=post_id)

    return render(
        request, "new.html", {"form": form, "post": post},
    )
    
@login_required
def add_comment(request, username, post_id):       
        post = get_object_or_404(Post, pk=post_id)
        if request.method == 'POST':
                form = CommentForm(request.POST)
                if form.is_valid():                      
                        Comment.objects.create(author=request.user, post=post, text=form.cleaned_data['text'])
        return redirect('post',username, post_id)

# Куда будут выведены посты авторов, на которых подписан текущий пользователь.
@login_required
def follow_index(request):
        f = Follow.objects.filter(user=request.user).values('author')
        post_list=Post.objects.select_related('author').filter(author__in=f).order_by("-pub_date")
        paginator = Paginator(post_list, 10)  
        page_number = request.GET.get('page')  
        page = paginator.get_page(page_number)  

        return render(request, 'follow.html', {'page': page, 'paginator': paginator})

# Подписки на интересного автора
@login_required
def profile_follow(request, username):
        author = User.objects.get(username=username)
        if request.user.username != username and Follow.objects.filter(user=request.user, author=author).count() == 0 :
                Follow.objects.create(user=request.user, author=author)
        return redirect('profile', username)

# Отписка от автора
@login_required
def profile_unfollow(request, username):
        author = User.objects.get(username=username)
        Follow.objects.filter(author=author).filter(user=request.user).delete()
        return redirect('profile', request.user.username)


def page_not_found(request, exception):
        # Переменная exception содержит отладочную информацию, 
        # выводить её в шаблон пользователской страницы 404 мы не станем
        return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
        return render(request, "misc/500.html", status=500)

        