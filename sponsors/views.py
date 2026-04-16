from django.views.generic import ListView
from .models import Sponsor


class SponsorListView(ListView):
    model = Sponsor
    template_name = 'sponsors/list.html'
    context_object_name = 'sponsors'

    def get_queryset(self):
        return Sponsor.objects.filter(active=True)
