from django.views.generic import DetailView, ListView

from .models import Team


class TeamListView(ListView):
    model = Team
    template_name = 'teams/list.html'
    context_object_name = 'teams'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = Team.objects.values_list('category', flat=True).distinct()
        context['by_category'] = {
            cat: Team.objects.filter(category=cat) for cat in categories
        }
        return context


class TeamDetailView(DetailView):
    model = Team
    template_name = 'teams/detail.html'
    context_object_name = 'team'
    slug_field = 'slug'
