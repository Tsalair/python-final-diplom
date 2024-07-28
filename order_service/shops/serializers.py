from rest_framework import serializers

from .models import Product, ProductInfo, Shop, Category


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "name", "url", "user", "is_accepting_orders"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = Product
        fields = ["id", "name", "category"]


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductSerializer()
    shop = ShopSerializer()

    class Meta:
        model = ProductInfo
        fields = [
            "id",
            "model",
            "external_id",
            "product",
            "shop",
            "quantity",
            "price",
            "price_rrc",
        ]
