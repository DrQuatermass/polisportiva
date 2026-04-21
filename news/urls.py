from django.urls import path
from .views import NewsDetailView, NewsListView, news_social_image

urlpatterns = [
    path('', NewsListView.as_view(), name='news_list'),
    path('<slug:slug>/social.jpg', news_social_image, name='news_social_image'),
    path('<slug:slug>/', NewsDetailView.as_view(), name='news_detail'),
]
