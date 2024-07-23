from django.db import models
from order_service.users.models import User

class Shop(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    url = models.URLField(verbose_name='Ссылка', null=True, blank=True)
    user = models.OneToOneField(User, verbose_name='Пользователь',
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    is_accepting_orders = models.BooleanField(verbose_name='Принимает заказы', default=True)

    class Meta:
        verbose_name = 'Магазин'
        verbose_name_plural = "Список магазинов"
        ordering = ('-name',)

    def __str__(self):
        return self.name

