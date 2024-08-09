from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestAddNote(TestCase):
    TITLE = 'Заголовок'
    TEXT = 'Текст'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.user = User.objects.create(username='Посетитель')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.author_note = Note.objects.create(
            title=cls.TITLE,
            text=cls.TEXT,
            slug='author_slug',
            author=cls.author
        )

    def test_authorized_user_has_form_for_note(self):
        """На страницы создания и редактирования заметки передаются формы."""
        for name, args in (
            ('notes:add', None),
            ('notes:edit', (self.author_note.slug,))
        ):
            with self.subTest(name=name):
                response = self.author_client.get(reverse(name, args=args))
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)

    def test_list_of_notes_contains_only_authors_notes(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок.
        В список заметок одного пользователя
        не попадают заметки другого пользователя.
        """
        for name, note_in_list in (
            (self.author_client, True),
            (self.user_client, False)
        ):
            with self.subTest(name=name):
                response = name.get(reverse('notes:list'))
                object_list = response.context['object_list']
                self.assertEqual(
                    (self.author_note in object_list), note_in_list
                )
