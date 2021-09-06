from django.apps import AppConfig


class MyappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'myapp'
    #注意这个名字需要和应用名保持一致，不要改
    #如果需要修改 app 在 admin 后台的显示名字，添加 verbose_name 属性。
    verbose_name = '博客'