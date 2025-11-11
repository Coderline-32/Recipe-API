from django.shortcuts import render
from .models import User
from .serializers import RegisterUserSerializers
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import redirect
from django.contrib.auth import authenticate

# Create your views here.

class RegisterUserView(APIView):

    def post(self, request):
        serializer = RegisterUserSerializers(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
               "message" : "User Created successfully"}, status = status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate (request, username = username, password = password)
        if user:
            return Response(
                {"message" : "Login Succesful"}, status = status.HTTP_200_OK
            )
        
        else:
            return Response(
                {
                    "message" : "Invalid credentials"
                }, status = status.HTTP_400_BAD_REQUEST
            )