from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from config.social_images import social_image_response

from .models import News


class NewsListView(ListView):
    model = News
    template_name = 'news/list.html'
    context_object_name = 'news_list'
    paginate_by = 9

    def get_queryset(self):
        return News.objects.filter(published=True)


class NewsDetailView(DetailView):
    model = News
    template_name = 'news/detail.html'
    context_object_name = 'news'
    slug_field = 'slug'


def news_social_image(request, slug):
    news = get_object_or_404(News, slug=slug)
    return social_image_response(news.og_image or news.image)
