from django.views.generic import DetailView, ListView

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
