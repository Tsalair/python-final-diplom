from rest_framework import generics

from order_service.shops.permissions import IsBuyer

from .serializers import ContactSerializer


class ContactList(generics.ListCreateAPIView):
    permission_classes = [IsBuyer]
    serializer_class = ContactSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        return user.contacts.all()


class ContactDetail(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsBuyer]
    serializer_class = ContactSerializer

    def get_queryset(self):
        user = self.request.user
        return user.contacts.all()
