from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from posts.models import Post, Group, Follow
from django.shortcuts import get_object_or_404
from django.conf import settings
import time



User = get_user_model()


# Create your tests here.

class ProfileTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="sarah", email="connor.s@skynet.com", password="12345678")
        self.another_user1 = User.objects.create_user(
            username="Joe", email="Joe.k@skynet.com", password="12345678")
        self.another_user2 = User.objects.create_user(
            username="Maria", email="Maria.w@skynet.com", password="12345678")
        self.test_post = "Test post from sarah"
        

    def test_page_profile(self):
        response = self.client.get("/sarah/")
        self.assertEqual(response.status_code, 200)

    def test_authorization_user_posting(self):
        self.client.login(username='sarah', password='12345678')
        self.client.post("/new/", {"text": self.test_post})
        response = self.client.get("/")
        self.assertContains(response, self.test_post)

    def test_unauthorized_user_cannot_post(self):
        # self.client.logout() # Не нужно разлогиневаться так как при переходе на новый тест я автоматом разлогинелся
        response = self.client.get('/new/')
        self.assertRedirects(response, '/')

    def test_new_post_appear_on_desired_pages(self):
        new = Post.objects.create(author=self.user, text=self.test_post)

        response = self.client.get("/")
        self.assertContains(response, self.test_post)

        response = self.client.get("/sarah/")
        self.assertContains(response, self.test_post)

        response = self.client.get(f"/sarah/{new.id}/")
        self.assertContains(response, self.test_post)

    def test_editing_end_checking_linked_pages(self):
        self.client.login(username='sarah', password='12345678')  # Логинюсь
        new = Post.objects.create(author=self.user, text=self.test_post)  # Создаю пост
        self.client.post(f"/sarah/{new.id}/edit/", {"text": "modified"})  # Редактирую пост
        self.assertEqual(Post.objects.get(author=self.user).text, "modified")  # Изменился ли пост

# Страницы с ошибками

    def test_not_found(self):
        response = self.client.get("/terminator/466/")
        self.assertEqual(response.status_code, 404)

# Добавление картинок к постам

    def test_img_tag_on_page(self):       
        self.client.login(username='sarah', password='12345678')
        with open('img_test/1.jpg','rb') as img:
            self.client.post("/new/", {'text': 'post with image', 'image': img})
        
        post = Post.objects.get( text='post with image')
        #print(post.id, post.image)
        response = self.client.get(f"/sarah/{post.id}/")
        self.assertContains(response, 'img')
        
    # Из-за кеширования нужно делать timesleep (тест с главной стр), если убрать кеширование в шаблоне index то всё будет ОК,
    #ИЛИ воспользоваться декоратором @override_settings с настройкой settings BACKEND!
    @override_settings(CACHES=settings.TEST_CACHES)  
    def test_post_with_picture_on_the_main_profile_group_pages(self):
        self.client.login(username='sarah', password='12345678')
        self.group = Group.objects.create(title='Test_group', slug='test_gr', description='It is test group')
        with open('img_test/1.jpg','rb') as img:
            self.client.post("/new/", {'text': 'post with image', 'image': img, 'group': self.group.id})
        post = Post.objects.get( text='post with image')
        response = self.client.get("/")
        self.assertContains(response, 'img')
        response = self.client.get(f'/{self.user.username}/')
        self.assertContains(response, 'img')
        response = self.client.get(f'/group/{self.group.slug}')
        self.assertContains(response, 'img')


    def test_non_graphical_file_download_protection(self):
        self.client.login(username='sarah', password='12345678')
        with open('img_test/wd.docx','rb') as img:
            response = self.client.post("/new/", {'text': 'post with image', 'image': img})
        self.assertEqual(response.status_code, 200)

    # Кеширование

    def test_cache(self):
        self.client.login(username='sarah', password='12345678')
        self.client.post("/new/", {"text": "Не появился ли текст сразу?"})
        response = self.client.get("/")
        self.assertNotContains(response, "Не появился ли текст сразу?")

    # Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок.

    def test_subscription_and_unsubscribing(self):
        self.client.login(username='sarah', password='12345678')
        response = self.client.get("/Joe/")
        self.assertContains(response, 'Подписаться')

        Follow.objects.create(user=self.user, author=self.another_user1)
        response = self.client.get("/Joe/")
        self.assertContains(response, 'Отписаться')

        Follow.objects.filter(author=self.another_user1).filter(user=self.user).delete()
        response = self.client.get("/Joe/")
        self.assertContains(response, 'Подписаться')

    # Новая запись пользователя появляется в ленте тех, кто на него подписан и не 
    # появляется в ленте тех, кто не подписан на него.

    def test_follow_html(self):
        Follow.objects.create(user=self.user, author=self.another_user1)
        Post.objects.create(author=self.another_user1, text='New')

        self.client.login(username='sarah', password='12345678')
        response = self.client.get("/follow/")
        self.assertContains(response, 'New')

        self.client.login(username='Maria', password='12345678')
        response = self.client.get("/follow/")
        with self.assertRaises(AssertionError):
            self.assertContains(response, 'New')

    # Только авторизированный пользователь может комментировать посты.

    def test_only_authorized_user_can_comment(self):
        self.client.login(username='sarah', password='12345678')
        new = Post.objects.create(author=self.another_user1, text='Test post')
        self.client.post(f'/{self.another_user1.username}/{new.id}/comment/', {"text": "Comment"})
        response = self.client.get(f'/{self.another_user1.username}/{new.id}/')
        self.assertContains(response, "Comment")

        with self.assertRaises(AttributeError):
            self.another_user2.post(f'/{self.another_user1.username}/{new.id}/comment/', {"text": "Comment"})
          
        






       
        


    





