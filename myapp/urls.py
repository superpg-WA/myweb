from django.urls import path

from . import views

"""
这里 <int:pk> 是 django 路由匹配规则的特殊写法，其作用是从用户访问的 
URL 里把匹配到的数字捕获并作为关键字参数传给其对应的视图函数 detail。
"""

app_name = 'myapp'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('posts/<int:pk>/', views.PostDetailView.as_view(), name='detail'),
    path('archives/<int:year>/<int:month>/', views.ArchiveView.as_view(), name='archive'),
    path('categories/<int:pk>/', views.CategoryView.as_view(), name='category'),
    path('tags/<int:pk>/', views.TagView.as_view(), name='tag'),
    path('search/', views.search, name='search'),
]

