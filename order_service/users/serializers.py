from rest_framework import serializers

from .models import Contact


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "user",
            "city",
            "street",
            "house",
            "structure",
            "building",
            "apartment",
            "phone",
        ]
