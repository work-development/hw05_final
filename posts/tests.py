from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from posts.models import Post, Group, Follow
from django.shortcuts import get_object_or_404
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
        

    def test_Page_Profile(self):
        response = self.client.get("/sarah/")
        self.assertEqual(response.status_code, 200)

    def test_Authorization_User_Posting(self):
        self.client.login(username='sarah', password='12345678')
        self.client.post("/new/", {"text": self.test_post})
        response = self.client.get("/")
        self.assertContains(response, self.test_post)

    def test_Unauthorized_User_Cannot_Post(self):
        # self.client.logout() # Не нужно разлогиневаться так как при переходе на новый тест я автоматом разлогинелся
        response = self.client.get('/new/')
        self.assertRedirects(response, '/')

    def test_New_Post_Appear_On_Desired_Pages(self):
        new = Post.objects.create(author=self.user, text=self.test_post)

        response = self.client.get("/")
        self.assertContains(response, self.test_post)

        response = self.client.get("/sarah/")
        self.assertContains(response, self.test_post)

        response = self.client.get(f"/sarah/{new.id}/")
        self.assertContains(response, self.test_post)

    def test_Editing_End_Checking_Linked_Pages(self):
        self.client.login(username='sarah', password='12345678')  # Логинюсь
        new = Post.objects.create(author=self.user, text=self.test_post)  # Создаю пост
        self.client.post(f"/sarah/{new.id}/edit", {"text": "modified"})  # Редактирую пост
        self.assertEqual(Post.objects.get(author=self.user).text, "modified")  # Изменился ли пост

# Страницы с ошибками

    def test_Not_Found(self):
        response = self.client.get("/terminator/466/")
        self.assertEqual(response.status_code, 404)

# Добавление картинок к постам

    def test_IMG_Tag_On_Page(self):       
        self.client.login(username='sarah', password='12345678')
        with open('img_test/1.jpg','rb') as img:
            self.client.post("/new/", {'text': 'post with image', 'image': img})
        
        post = Post.objects.get( text='post with image')
        #print(post.id, post.image)
        response = self.client.get(f"/sarah/{post.id}/")
        self.assertContains(response, 'img')
        
    # Из-за кеширования нужно делать timesleep (тест с главной стр), если убрать кеширование в шаблоне index то всё будет ОК
    def test_Post_With_Picture_On_The_Main_Profile_Group_Pages(self):
        self.client.login(username='sarah', password='12345678')
        self.group = Group.objects.create(title='Test_group', slug='test_gr', description='It is test group')
        with open('img_test/1.jpg','rb') as img:
            self.client.post("/new/", {'text': 'post with image', 'image': img, 'group': self.group.id})
        post = Post.objects.get( text='post with image')
        print(post.id, post.image, post.group)
        time.sleep(20) # ЖДЕМ ЧТОБЫ ПОСТ ПОЯВИЛСЯ ПОСЛЕ КЕШИРОВАНИЯ
        response = self.client.get("/")
        #print(response.content.decode('utf-8')
        self.assertContains(response, 'img')
        response = self.client.get(f'/{self.user.username}/')
        self.assertContains(response, 'img')
        response = self.client.get(f'/group/{self.group.slug}')
        self.assertContains(response, 'img')

    def test_Non_Graphical_File_Download_Protection(self):
        self.client.login(username='sarah', password='12345678')
        with self.assertRaises(ValueError):
            with open('img_test/wd.docx','rb') as img:
                self.client.post("/new/", {'text': 'post with image', 'image': img})

    # Кеширование

    def test_Cache(self):
        self.client.login(username='sarah', password='12345678')
        self.client.post("/new/", {"text": "Не появился ли текст сразу?"})
        response = self.client.get("/")
        with self.assertRaises(AssertionError):
            self.assertContains(response, "Не появился ли текст сразу?")

    # Авторизованный пользователь может подписываться на других пользователей и удалять их из подписок.

    def test_Subscription_And_Unsubscribing(self):
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

    def test_Follow_HTML(self):
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

    def test_Only_Authorized_User_Can_Comment(self):
        self.client.login(username='sarah', password='12345678')
        new = Post.objects.create(author=self.another_user1, text='Test post')
        self.client.post(f'/{self.another_user1.username}/{new.id}/comment/', {"text": "Comment"})
        response = self.client.get(f'/{self.another_user1.username}/{new.id}/')
        self.assertContains(response, "Comment")

        with self.assertRaises(AttributeError):
            self.another_user2.post(f'/{self.another_user1.username}/{new.id}/comment/', {"text": "Comment"})
          
        






       
        


    





