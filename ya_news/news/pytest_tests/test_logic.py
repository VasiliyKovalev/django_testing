from http import HTTPStatus

import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(
    client, form_data, news_detail_url
):
    """Анонимный пользователь не может отправить комментарий."""
    client.post(news_detail_url, data=form_data)
    assert Comment.objects.count() == 0


def test_user_can_create_comment(
    author, author_client, form_data, news, news_detail_url, url_to_comments
):
    """Авторизованный пользователь может отправить комментарий."""
    response = author_client.post(news_detail_url, data=form_data)
    assertRedirects(response, url_to_comments)
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


@pytest.mark.parametrize(
    'bad_word',
    BAD_WORDS,
)
def test_user_cant_use_bad_words(author_client, bad_word, news_detail_url):
    """
    Если комментарий содержит запрещённые слова, он не будет опубликован.
    Форма вернёт ошибку.
    """
    bad_words_data = {'text': f'Какой-то текст, {bad_word}, еще текст'}
    response = author_client.post(news_detail_url, data=bad_words_data)
    assertFormError(
        response,
        'form',
        'text',
        errors=WARNING
    )
    assert Comment.objects.count() == 0


def test_author_can_delete_comment(
    author_client, comment_delete_url, url_to_comments
):
    """Авторизованный пользователь может удалять свои комментарии."""
    response = author_client.delete(comment_delete_url)
    assertRedirects(response, url_to_comments)
    assert Comment.objects.count() == 0


def test_user_cant_delete_comment_of_another_user(
    reader_client, comment_delete_url
):
    """
    Авторизованный пользователь не может удалять чужие комментарии.
    При попытке возвращается ошибка 404.
    """
    response = reader_client.delete(comment_delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


def test_author_can_edit_comment(
    author,
    author_client,
    comment,
    comment_edit_url,
    form_data,
    news,
    url_to_comments
):
    """Авторизованный пользователь может редактировать свои комментарии."""
    response = author_client.post(comment_edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


def test_user_cant_edit_comment_of_another_user(
    author, comment, comment_edit_url, form_data, news, reader_client
):
    """
    Авторизованный пользователь не может редактировать чужие комментарии.
    При попытке возвращается ошибка 404.
    """
    initial_comment_text = comment.text
    response = reader_client.post(comment_edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == initial_comment_text
    assert comment.news == news
    assert comment.author == author
