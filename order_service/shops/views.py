import requests
import yaml
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Category,
    Parameter,
    Product,
    ProductInfo,
    ProductInfoParameter,
    Shop,
)
from .permissions import IsShop
from .serializers import ProductInfoSerializer, ShopSerializer


class PartnerUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """

    permission_classes = [IsShop]

    def post(self, request, *args, **kwargs):
        url = request.data.get("url")
        if not url:
            return JsonResponse(
                {"Status": False, "Errors": "Не указаны все необходимые аргументы"}
            )

        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as e:
            return JsonResponse({"Status": False, "Error": str(e)})

        stream = requests.get(url).content

        data = yaml.safe_load(stream)

        shop, _ = Shop.objects.get_or_create(
            user_id=request.user.id, defaults={"name": data["shop"]}
        )
        for category in data["categories"]:
            category_object, _ = Category.objects.get_or_create(
                id=category["id"], defaults={"name": category["name"]}
            )
            category_object.shops.add(shop.id)
            category_object.save()

        # TODO: добавить обновление информации о продуктах
        shop.product_infos.all().delete()

        for item in data["goods"]:
            product, _ = Product.objects.get_or_create(
                name=item["name"], defaults={"category_id": item["category"]}
            )

            product_info = ProductInfo.objects.create(
                product_id=product.id,
                external_id=item["id"],
                model=item["model"],
                price=item["price"],
                price_rrc=item["price_rrc"],
                quantity=item["quantity"],
                shop_id=shop.id,
            )
            for name, value in item["parameters"].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductInfoParameter.objects.create(
                    product_info_id=product_info.id,
                    parameter_id=parameter_object.id,
                    value=value,
                )

        return JsonResponse({"Status": True})


class ShopList(generics.ListAPIView):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class ProductInfoList(generics.ListAPIView):
    serializer_class = ProductInfoSerializer

    def get_queryset(self):
        queryset = ProductInfo.objects.prefetch_related("product__category", "shop")
        shop_id = self.request.query_params.get("shop_id")
        category_id = self.request.query_params.get("category_id")

        if shop_id is not None:
            queryset = queryset.filter(shop_id=shop_id)
        if category_id is not None:
            queryset = queryset.filter(product__category_id=category_id)

        return queryset


class PartnerState(APIView):
    permission_classes = [IsShop]

    def get(self, request):
        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)
