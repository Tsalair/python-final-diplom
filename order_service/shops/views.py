import requests
import yaml
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import URLValidator
from django.db.models import F, Sum
from django.http import JsonResponse
from rest_framework import generics
from rest_framework.exceptions import ParseError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Category,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductInfoParameter,
    Shop,
)
from .permissions import IsBuyer, IsShop
from .serializers import (
    BasketAddSerializer,
    BasketDeleteSerializer,
    BasketUpdateSerializer,
    CategorySerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductInfoSerializer,
    ShopSerializer,
)


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


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


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

    def post(self, request):
        shop = request.user.shop
        serializer = ShopSerializer(shop, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class Basket(APIView):
    permission_classes = [IsBuyer]

    def _get_order_items(self, basket):
        order_items = basket.ordered_items.prefetch_related(
            "product_info__product__category", "product_info__shop"
        )
        serializer = OrderItemSerializer(order_items, many=True)
        return Response(serializer.data)

    def post(self, request):
        basket, _ = request.user.orders.get_or_create(state="basket")

        serializer = BasketAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for order_item in data["items"]:
            product_info_id = order_item["product_info"]
            if not ProductInfo.objects.filter(id=product_info_id).exists():
                raise ParseError(f"Product info {product_info_id} does not exist")

            order_item, _ = basket.ordered_items.update_or_create(
                product_info_id=product_info_id,
                create_defaults={"quantity": order_item["quantity"]},
                defaults={"quantity": F("quantity") + order_item["quantity"]},
            )

        return self._get_order_items(basket)

    def put(self, request):
        try:
            basket = request.user.orders.get(state="basket")
        except Order.DoesNotExist:
            raise ParseError("Basket does not exist")

        serializer = BasketUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for order_item in data["items"]:
            try:
                order_item_object = basket.ordered_items.get(id=order_item["id"])
            except OrderItem.DoesNotExist:
                raise ParseError(f"Order item {order_item['id']} does not exist")

            order_item_object.quantity = order_item["quantity"]
            order_item_object.save()

        return self._get_order_items(basket)

    def get(self, request):
        try:
            basket = request.user.orders.get(state="basket")
        except Order.DoesNotExist:
            raise ParseError("Basket does not exist")

        return self._get_order_items(basket)

    def delete(self, request):
        try:
            basket = request.user.orders.get(state="basket")
        except Order.DoesNotExist:
            raise ParseError("Basket does not exist")

        serializer = BasketDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for order_item in data["items"]:
            try:
                order_item_object = basket.ordered_items.get(id=order_item)
            except OrderItem.DoesNotExist:
                raise ParseError(f"Order item {order_item} does not exist")

            order_item_object.delete()

        return self._get_order_items(basket)


class Orders(APIView):
    permission_classes = [IsBuyer]

    def post(self, request):
        try:
            order = request.user.orders.annotate(
                total=Sum(
                    F("ordered_items__product_info__price")
                    * F("ordered_items__quantity")
                )
            ).get(state="basket")

        except Order.DoesNotExist:
            raise ParseError("Basket does not exist")

        serializer = OrderSerializer(order, data=request.data)
        serializer.is_valid(raise_exception=True)
        contact = serializer.validated_data["contact"]
        
        if contact.user_id != request.user.id:
            raise ParseError("Contact does not exist")
        serializer.save(state="new")

        send_mail("New order", "Thank you for your order!", None, [request.user.email])
        return Response(OrderSerializer(order).data)

    def get(self, request):
        orders = request.user.orders.exclude(state="basket").annotate(
            total=Sum(
                F("ordered_items__product_info__price") * F("ordered_items__quantity")
            )
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
