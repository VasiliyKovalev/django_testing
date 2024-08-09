from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News


NEWS_COUNT = settings.NEWS_COUNT_ON_HOME_PAGE + 1
COMMENTS_COUNT = 10


@pytest.fixture
def news():
    return News.objects.create(title='Заголовок', text='Текст',)


@pytest.fixture
def some_news():
    today = datetime.today()
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index)
        )
        for index in range(NEWS_COUNT)
    ]
    News.objects.bulk_create(all_news)


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель')


@pytest.fixture
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def reader_client(reader):
    client = Client()
    client.force_login(reader)
    return client


@pytest.fixture
def comment(author, news):
    return Comment.objects.create(
        news=news,
        author=author,
        text='Текст комментария'
    )


@pytest.fixture
def some_comments(author, news):
    now = timezone.now()
    for index in range(COMMENTS_COUNT):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()


@pytest.fixture
def news_id(news):
    return (news.id,)


@pytest.fixture
def form_data():
    return {'text': 'Новый текст комментария'}


@pytest.fixture
def news_detail_url(news):
    return reverse('news:detail', args=(news.id,))


@pytest.fixture
def url_to_comments(news_detail_url):
    return news_detail_url + '#comments'


@pytest.fixture
def comment_edit_url(comment):
    return reverse('news:edit', args=(comment.id,))


@pytest.fixture
def comment_delete_url(comment):
    return reverse('news:delete', args=(comment.id,))
