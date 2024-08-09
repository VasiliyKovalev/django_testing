from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestNoteCreate(TestCase):
    """Класс тестирования создания заметок."""
    TITLE = 'Заголовок'
    TEXT = 'Текст'
    SLUG = 'unique_slug'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Автор')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.TITLE,
            'text': cls.TEXT,
            'slug': cls.SLUG
        }
        cls.form_data_without_slug = {
            'title': cls.TITLE,
            'text': cls.TEXT,
        }
        cls.create_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        initial_notes_count = Note.objects.count()
        self.client.post(self.create_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, initial_notes_count)

    def test_authorized_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        Note.objects.all().delete()
        response = self.user_client.post(
            self.create_url,
            data=self.form_data
        )
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.title, self.form_data['title'])
        self.assertEqual(note.text, self.form_data['text'])
        self.assertEqual(note.slug, self.form_data['slug'])
        self.assertEqual(note.author, self.user)

    def test_authorized_user_can_create_note_without_slug(self):
        """
        Авторизованный пользователь может создать заметку, не указывая slug.
        Slug формируется автоматически из заголовка.
        """
        Note.objects.all().delete()
        response = self.user_client.post(
            self.create_url,
            data=self.form_data_without_slug
        )
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.slug = slugify(self.TITLE)
        self.assertEqual(note.slug, self.slug)

    def test_authorized_user_cant_create_note_with_not_unique_slug(self):
        """Невозможно создать две заметки с одинаковым slug."""
        note = Note.objects.create(
            title=self.TITLE,
            text=self.TEXT,
            slug=self.SLUG,
            author=self.user
        )
        initial_notes_count = Note.objects.count()
        self.form_data['slug'] = note.slug
        response = self.user_client.post(
            self.create_url,
            data=self.form_data
        )
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.SLUG + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, initial_notes_count)


class TestNoteEditDelete(TestCase):
    """Класс тестирования редактирования и удаления заметок."""
    TITLE = 'Заголовок'
    TEXT = 'Текст'
    SLUG = 'unique_slug'

    NEW_TITLE = 'Измененный заголовок'
    NEW_TEXT = 'Измененный текст'
    NEW_SLUG = 'new_slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.user = User.objects.create(username='Посетитель')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.note = Note.objects.create(
            title=cls.TITLE,
            text=cls.TEXT,
            slug=cls.SLUG,
            author=cls.author
        )
        cls.form_data = {
            'title': cls.NEW_TITLE,
            'text': cls.NEW_TEXT,
            'slug': cls.NEW_SLUG
        }
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')

    def test_author_can_delete_note(self):
        """Пользователь может удалять свои заметки."""
        initial_notes_count = Note.objects.count()
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, initial_notes_count - 1)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалять чужие заметки."""
        initial_notes_count = Note.objects.count()
        response = self.user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, initial_notes_count)

    def test_author_can_edit_note(self):
        """Пользователь может редактировать свои заметки."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать свои заметки."""
        response = self.user_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.TITLE)
        self.assertEqual(self.note.text, self.TEXT)
        self.assertEqual(self.note.slug, self.SLUG)
