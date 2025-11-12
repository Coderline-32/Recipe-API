from django.shortcuts import render
from .models import User
from .serializers import RegisterUserSerializers, UserSerializer
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout


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
            login(request, user)
            return Response(
                {"message" : "Login Succesful"}, status = status.HTTP_200_OK
            )
        
        else:
            return Response(
                {
                    "message" : "Invalid credentials"
                }, status = status.HTTP_400_BAD_REQUEST
            )
        
class UsersView(ListAPIView):
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserSerializer

class UserProfileView(RetrieveAPIView):
   permission_classes = [IsAuthenticated]

   def get(self, request):
       serializer = UserSerializer(request.user)
       return Response(serializer.data)



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'message':'Logout succesful'}, status = status.HTTP_200_OK
        )