import re
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
import markdown
from django.utils.html import strip_tags
from django.utils.functional import cached_property
from django.utils.text import slugify
from markdown.extensions.toc import TocExtension

#解析 markdown 文本，并将得到的内容 HTML 和 目录toc 一起返回。
def generate_rich_content(value):
    md = markdown.Markdown(
        extensions=[
            "markdown.extensions.extra",
            "markdown.extensions.codehilite",
            # 记得在顶部引入 TocExtension 和 slugify
            TocExtension(slugify=slugify),
        ]
    )
    content = md.convert(value)
    m = re.search(r'<div class="toc">\s*<ul>(.*)</ul>\s*</div>', md.toc, re.S)
    toc = m.group(1) if m is not None else ""
    return {"content": content, "toc": toc}


class Category(models.Model):
    """
    django 要求模型必须继承 models.Model 类。
    Category 只需要一个简单的分类名 name 就可以了。
    CharField 指定了分类名 name 的数据类型，CharField 是字符型，
    CharField 的 max_length 参数指定其最大长度，超过这个长度的分类名就不能被存入数据库。
    当然 django 还为我们提供了多种其它的数据类型，如日期时间类型 DateTimeField、整数类型 IntegerField 等等。
    django 内置的全部类型可查看文档：
    https://docs.djangoproject.com/en/2.2/ref/models/fields/#field-types
    """
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

class Tag(models.Model):
    """
    标签 Tag 也比较简单，和 Category 一样。
    再次强调一定要继承 models.Model 类！
    """
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = '标签'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

#给每个 Field 都传入了一个位置参数，参数值即为 field 应该显示的名字
class Post(models.Model):
    """
    文章的数据库表稍微复杂一点，主要是涉及的字段更多。
    """

    # 文章标题
    title = models.CharField('标题',max_length=70)

    # 文章正文，我们使用了 TextField。
    # 存储比较短的字符串可以使用 CharField，但对于文章的正文来说可能会是一大段文本，因此使用 TextField 来存储大段文本。
    body = models.TextField('正文')

    # 这两个列分别表示文章的创建时间和最后一次修改时间，存储时间的字段用 DateTimeField 类型。
    """
    Model 中定义的每个 Field 都接收一个 default 关键字参数，这个参数的含义是，
    如果将 model 的实例保存到数据库时，对应的 Field 没有设置值，
    那么 django 会取这个 default 指定的默认值，将其保存到数据库。
    因此，对于文章创建时间这个字段，初始没有指定值时，默认应该指定为当前时间，
    所以刚好可以通过 default 关键字参数指定。
    
    调用的timezone模块是 Django 提供的，能自动处理时区问题。
    """
    created_time = models.DateTimeField('创建时间', default=timezone.now)
    modified_time = models.DateTimeField('修改时间')

    # 文章摘要，可以没有文章摘要，但默认情况下 CharField 要求我们必须存入数据，否则就会报错。
    # 指定 CharField 的 blank=True 参数值后就可以允许空值了。
    excerpt = models.CharField('摘要',max_length=200, blank=True)

    # 这是分类与标签，分类与标签的模型我们已经定义在上面。
    # 我们在这里把文章对应的数据库表和分类、标签对应的数据库表关联了起来，但是关联形式稍微有点不同。
    # 我们规定一篇文章只能对应一个分类，但是一个分类下可以有多篇文章，所以我们使用的是 ForeignKey，即一
    # 对多的关联关系。且自 django 2.0 以后，ForeignKey 必须传入一个 on_delete 参数用来指定当关联的
    # 数据被删除时，被关联的数据的行为，我们这里假定当某个分类被删除时，该分类下全部文章也同时被删除，因此     # 使用 models.CASCADE 参数，意为级联删除。
    # 而对于标签来说，一篇文章可以有多个标签，同一个标签下也可能有多篇文章，所以我们使用
    # ManyToManyField，表明这是多对多的关联关系。
    # 同时我们规定文章可以没有标签，因此为标签 tags 指定了 blank=True。
    # 如果你对 ForeignKey、ManyToManyField 不了解，请看教程中的解释，亦可参考官方文档：
    # https://docs.djangoproject.com/en/2.2/topics/db/models/#relationships
    category = models.ForeignKey(Category, verbose_name='分类', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, verbose_name='标签', blank=True)

    # 文章作者，这里 User 是从 django.contrib.auth.models 导入的。
    # django.contrib.auth 是 django 内置的应用，专门用于处理网站用户的注册、登录等流程，User 是
    # django 为我们已经写好的用户模型。
    # 这里我们通过 ForeignKey 把文章和 User 关联了起来。
    # 因为我们规定一篇文章只能有一个作者，而一个作者可能会写多篇文章，因此这是一对多的关联关系，和
    # Category 类似。
    author = models.ForeignKey(User, verbose_name='作者', on_delete=models.CASCADE)

    #views变量记录阅览量
    """
    views 字段的类型为 PositiveIntegerField，该类型的值只允许为正整数或 0，因为阅读量不可能为负值。
    初始化时 views 的值为 0。将 editable 参数设为 False 将不允许通过 django admin 后台编辑此字段的内容。
    因为阅读量应该根据被访问次数统计，而不应该人为修改。
    """
    views = models.PositiveIntegerField(default=0, editable=False)

    #让文章类在后台能显示中文名字
    class Meta:
        verbose_name = '文章'
        #复数形式
        verbose_name_plural = verbose_name
        #默认排序方法
        ordering = ['-created_time']

    def __str__(self):
        return self.title

    """
    由于 modified_time 已经有值，即第一次的默认值，那么第二次保存时默认值就不会起作用了，
    如果我们不修改 modified_time 的值的话，其值永远是第一次保存数据库时的默认值。
    
    每一个 Model 都有一个 save 方法，这个方法包含了将 model 数据
    保存到数据库中的逻辑。通过覆写这个方法，在 model 被 save 到数据库前
    指定 modified_time 的值为当前时间即可。
    """
    def save(self, *args, **kwargs):
        self.modified_time = timezone.now()

        # 首先实例化一个 Markdown 类，用于渲染 body 的文本。
        # 由于摘要并不需要生成文章目录，所以去掉了目录拓展。
        md = markdown.Markdown(extensions=[
            'markdown.extensions.extra',
            'markdown.extensions.codehilite',
        ])

        # 先将 Markdown 文本渲染成 HTML 文本
        # strip_tags 去掉 HTML 文本的全部 HTML 标签
        # 从文本摘取前 54 个字符赋给 excerpt
        self.excerpt = strip_tags(md.convert(self.body))[:54]

        super().save(*args, **kwargs)

    # 自定义 get_absolute_url 方法
    # 记得从 django.urls 中导入 reverse 函数
    def get_absolute_url(self):
        return reverse('myapp:detail', kwargs={'pk': self.pk})

    #注意这里使用了 update_fields 参数来告诉 Django 只更新数据库中 views 字段的值，以提高效率。
    def increase_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    """
    cached_property 进一步提供缓存功能，它将被装饰方法调用返回的值缓存起来，下次访问时将直接读取缓存内容，
    而不需重复执行方法获取返回结果。
    """

    @property
    def toc(self):
        return self.rich_content.get("toc", "")

    @property
    def body_html(self):
        return self.rich_content.get("content", "")

    @cached_property
    def rich_content(self):
        return generate_rich_content(self.body)