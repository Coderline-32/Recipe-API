from django.urls import path
from .views import RegisterUserView, LoginView, UsersView, UserProfileView


urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='user_register'),
    path('login/', LoginView.as_view(), name='login'),
    path('users/', UsersView.as_view(), name="users_list"),
    path('me/', UserProfileView.as_view(), name="user_profile"),

]