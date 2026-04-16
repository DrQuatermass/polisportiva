from django.views.generic import DetailView, TemplateView

from .models import Document


class DocumentListView(TemplateView):
    template_name = 'documents/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        docs = Document.objects.filter(active=True)
        context['regolamenti'] = docs.filter(category='regolamento')
        context['etico'] = docs.filter(category='etico')
        context['safeguarding'] = docs.filter(category='safeguarding')
        context['privacy'] = docs.filter(category='privacy')
        context['promo'] = docs.filter(category='promo')
        return context


class DocumentDetailView(DetailView):
    model = Document
    template_name = 'documents/detail.html'
    context_object_name = 'doc'
    queryset = Document.objects.filter(active=True)
