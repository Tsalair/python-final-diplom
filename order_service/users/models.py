from authemail.models import EmailAbstractUser, EmailUserManager
from django.db import models

USER_TYPE_CHOICES = (
    ("shop", "Магазин"),
    ("buyer", "Покупатель"),
)


# class UserManager(BaseUserManager):

#     def _create_user(self, email, password, **extra_fields):
#         """
#         Create and save a user with the given username, email, and password.
#         """
#         if not email:
#             raise ValueError('Поле "email" обязательно для заполнения')
#         email = self.normalize_email(email)
#         user = self.model(email=email, **extra_fields)
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_user(self, email, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', False)
#         extra_fields.setdefault('is_superuser', False)
#         return self._create_user(email, password, **extra_fields)

#     def create_superuser(self, email, password, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self._create_user(email, password, **extra_fields)


class User(EmailAbstractUser):
    objects = EmailUserManager()
    company = models.CharField(verbose_name="Компания", max_length=40, blank=True)
    position = models.CharField(verbose_name="Должность", max_length=40, blank=True)
    type = models.CharField(
        verbose_name="Тип пользователя",
        choices=USER_TYPE_CHOICES,
        max_length=5,
        default="buyer",
    )

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Список пользователей"
        ordering = ("email",)


class Contact(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name="Пользователь",
        related_name="contacts",
        blank=True,
        on_delete=models.CASCADE,
    )

    city = models.CharField(max_length=50, verbose_name="Город")
    street = models.CharField(max_length=100, verbose_name="Улица")
    house = models.CharField(max_length=15, verbose_name="Дом", blank=True)
    structure = models.CharField(max_length=15, verbose_name="Корпус", blank=True)
    building = models.CharField(max_length=15, verbose_name="Строение", blank=True)
    apartment = models.CharField(max_length=15, verbose_name="Квартира", blank=True)
    phone = models.CharField(max_length=20, verbose_name="Телефон")

    class Meta:
        verbose_name = "Контакты пользователя"
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f"{self.city} {self.street} {self.house}"
