import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm


@pytest.mark.django_db
@pytest.mark.usefixtures('some_news')
def test_news_count(client):
    """
    Максимальное количество новостей на главной странице
    равно заданному значению.
    """
    url = reverse('news:home')
    response = client.get(url)
    assert 'object_list' in response.context
    object_list = response.context['object_list']
    assert len(object_list) == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
@pytest.mark.usefixtures('some_news')
def test_news_order(client):
    """
    Новости отсортированы от самой свежей к самой старой.
    Свежие новости в начале списка.
    """
    url = reverse('news:home')
    response = client.get(url)
    assert 'object_list' in response.context
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


@pytest.mark.usefixtures('some_comments')
def test_comments_order(client, news_detail_url):
    """
    Комментарии на странице отдельной новости
    отсортированы в хронологическом порядке:
    старые в начале списка, новые — в конце.
    """
    response = client.get(news_detail_url)
    assert 'news' in response.context
    news = response.context['news']
    all_comments = news.comment_set.all()
    all_timestamps = [comment.created for comment in all_comments]
    sorted_timestamps = sorted(all_timestamps)
    assert all_timestamps == sorted_timestamps


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, news_detail_url):
    """
    Анонимному пользователю недоступна форма для отправки комментария
    на странице отдельной новости.
    """
    response = client.get(news_detail_url)
    assert 'form' not in response.context


def test_authorized_client_has_form(author_client, news_detail_url):
    """
    Авторизованному пользователю доступна форма для отправки комментария
    на странице отдельной новости.
    """
    response = author_client.get(news_detail_url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
