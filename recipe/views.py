from django.shortcuts import render
from rest_framework import generics
from .models import Recipe
from .serializers import RecipeSerializers
from rest_framework.permissions import IsAuthenticated


class RecipeListView(generics.ListAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

class RecipeCreateView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RecipeDetailView(generics.RetrieveAPIView):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

class RecipeDetailUpdateView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializers

    def get_query(self):
        return Recipe.objects.filter(user = self.request.user)



