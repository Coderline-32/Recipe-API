from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class RegisterUserSerializers(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type':'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password":"Passwords don't match!"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            username=validated_data['email'],   # ✅ add this line
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

    