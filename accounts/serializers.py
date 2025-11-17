from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class RegisterUserSerializers(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type':'password'}, write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']

    def validate(self, attrs):
        missing_fields = [field for field in self.fields if field not in attrs or not attrs[field]]
        
        if missing_fields:
            # Build a readable error message
            raise serializers.ValidationError({
                "missing_fields": [f"{field} is required" for field in missing_fields]
            })

        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password":"Passwords don't match!"})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=validated_data['username'],   # ✅ add this line
            email=validated_data['email'],
            password=password
            
        )
        
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email"]