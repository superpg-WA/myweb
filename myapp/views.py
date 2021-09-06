from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import Post, Category, Tag
import markdown
#使用正则表达式需要引入 re 模块
import re
from django.utils.text import slugify
from markdown.extensions.toc import TocExtension

# Create your views here.

def index(request):
    post_list = Post.objects.all().order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})

#index.html 所在blog文件夹是在tempaltes里的。


def archive(request, year, month):
    post_list = Post.objects.filter(created_time__year=year,
                                    created_time__month=month
                                    ).order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})


def detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    md = markdown.Markdown(extensions=[
                                      'markdown.extensions.extra',
                                      'markdown.extensions.fenced_code',
                                      TocExtension(slugify=slugify),
                                  ])
    post.body = md.convert(post.body)
    # 阅读量 +1
    post.increase_views()
    """
    分析 toc 的内容，如果有目录结构，ul 标签中就有值，否则就没有值。
    我们可以使用正则表达式来测试 ul 标签中是否包裹有元素来确定是否存在目录。
    """

    m = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', md.toc, re.S)
    post.toc = m.group(1) if m is not None else ''

    """
    这里我们正则表达式去匹配生成的目录中包裹在 ul 标签中的内容，如果不为空，说明有目录，
    就把 ul 标签中的值提取出来（目的是只要包含目录内容的最核心部分，
    多余的 HTML 标签结构丢掉）赋值给 post.toc；否则，将 post 的 toc 置为空字符串，
    然后我们就可以在模板中通过判断 post.toc 是否为空，来决定是否显示侧栏目录：
    """

    return render(request, 'blog/detail.html', context={'post': post})

def category(request, pk):
    # 记得在开始部分导入 Category 类
    cate = get_object_or_404(Category, pk=pk)
    post_list = Post.objects.filter(category=cate).order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})

def tag(request, pk):
    # 记得在开始部分导入 Tag 类
    t = get_object_or_404(Tag, pk=pk)
    post_list = Post.objects.filter(tags=t).order_by('-created_time')
    return render(request, 'blog/index.html', context={'post_list': post_list})