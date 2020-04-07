from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(max_length=10000)

    def __str__(self):
        # выводим название группы там где на это запрос пойдет
        return self.title

class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("Дата публикации", auto_now_add=True, db_index=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="author_posts")
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="group_posts", blank=True, null=True
    )
    # поле для картинки
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        # выводим текст поста 
        return self.text

class Comment(models.Model):
    post = models.ForeignKey(Post, blank=True, null=True, on_delete=models.CASCADE, related_name="post")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comment_author")
    text = models.TextField()
    created = models.DateTimeField("Дата публикации", auto_now_add=True, db_index=True)

class Follow(models.Model):
    user = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE, related_name="follower") #который подписывается
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")

    def __str__(self):
        return f'follower - {self.user} following - {self.author}'
