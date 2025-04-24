# users/serializers.py
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from .models import UserProfile, CustomUser
import random
import string


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'date_of_birth', 'gender', 'occupation', 
                 'next_of_kin', 'next_of_kin_contact', 'id_front_image', 
                 'id_back_image', 'passport_photo', 'signature', 'documents_verified']
        read_only_fields = ['documents_verified']


class ProfileSerializer(serializers.ModelSerializer):
    profile_picture_url = serializers.SerializerMethodField()
    id_front_image_url = serializers.SerializerMethodField()
    id_back_image_url = serializers.SerializerMethodField()
    passport_photo_url = serializers.SerializerMethodField()
    signature_url = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'date_of_birth', 
            'gender', 
            'occupation',
            'next_of_kin',
            'next_of_kin_contact',
            'profile_picture',
            'profile_picture_url',
            'id_front_image',
            'id_front_image_url',
            'id_back_image',
            'id_back_image_url',
            'passport_photo',
            'passport_photo_url',
            'signature',
            'signature_url'
        ]

    def get_profile_picture_url(self, obj):
        return self._get_image_url(obj.profile_picture)

    def get_id_front_image_url(self, obj):
        return self._get_image_url(obj.id_front_image)

    def get_id_back_image_url(self, obj):
        return self._get_image_url(obj.id_back_image)

    def get_passport_photo_url(self, obj):
        return self._get_image_url(obj.passport_photo)

    def get_signature_url(self, obj):
        return self._get_image_url(obj.signature)

    def _get_image_url(self, image):
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.url)
        return None


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 'id_number', 'email', 'first_name', 'last_name',
            'phone_number', 'user_type', 'is_active', 'is_first_login'
        ]
        read_only_fields = ['id', 'id_number']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['id_number', 'email', 'password', 'first_name', 'last_name', 
                 'phone_number', 'address', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            password=password,
            **validated_data
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        validate_password(value)
        return value


class AdminPasswordChangeSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        validate_password(value)
        return value
    
    def validate_user_id(self, value):
        try:
            CustomUser.objects.get(id_number=value)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("User with this ID number does not exist")
        return value


class UpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for updating user details"""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'address']


class AdminUpdateUserSerializer(serializers.ModelSerializer):
    """Serializer for admin to update any user details including phone number"""
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'is_active']


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile details"""
    class Meta:
        model = UserProfile
        fields = [
            'profile_picture', 'date_of_birth', 'gender', 'occupation',
            'next_of_kin', 'next_of_kin_contact', 'id_front_image',
            'id_back_image', 'passport_photo', 'signature',
            'verification_status', 'verification_notes',
            'id_front_verified', 'id_back_verified',
            'passport_photo_verified', 'signature_verified'
        ]
        read_only_fields = [
            'verification_status', 'verification_notes',
            'id_front_verified', 'id_back_verified',
            'passport_photo_verified', 'signature_verified'
        ]


class DocumentVerificationSerializer(serializers.ModelSerializer):
    """Serializer for admin to verify user documents"""
    class Meta:
        model = UserProfile
        fields = ['documents_verified']
        read_only_fields = ['profile_picture', 'date_of_birth', 'gender', 'occupation', 
                           'next_of_kin', 'next_of_kin_contact', 'id_front_image', 
                           'id_back_image', 'passport_photo', 'signature']


class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=6, min_length=6)