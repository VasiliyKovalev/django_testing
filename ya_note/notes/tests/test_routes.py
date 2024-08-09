from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Посетитель')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )
        cls.note_slug_for_args = (cls.note.slug,)

    def test_pages_availability(self):
        """
        Главная страница, страницы регистрации пользователей,
        входа в учётную запись и выхода из неё доступны всем пользователям.
        """
        for name in (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        ):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_availability(self):
        """
        Авторизованному пользователю доступна страница со списком заметок,
        страница добавления новой заметки,
        страница успешного добавления заметки.
        """
        for name in (
            'notes:list',
            'notes:add',
            'notes:success'
        ):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_detail_and_edit_and_delete(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки
        доступны только автору заметки.
        Попытка другого пользователя зайти на эти страницы вернёт ошибку 404.
        """
        users_statuses = (
            (self.author_client, HTTPStatus.OK),
            (self.reader_client, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            for name in (
                'notes:detail',
                'notes:edit',
                'notes:delete'
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=self.note_slug_for_args)
                    response = user.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок,
        страницу добавления заметки, страницу успешного добавления записи,
        отдельной заметки, редактирования или удаления заметки
        анонимный пользователь перенаправляется на страницу логина.
        """
        login_url = reverse('users:login')
        for name, args in (
            ('notes:list', None),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:detail', self.note_slug_for_args),
            ('notes:edit', self.note_slug_for_args),
            ('notes:delete', self.note_slug_for_args)
        ):
            with self.subTest(name=name):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
