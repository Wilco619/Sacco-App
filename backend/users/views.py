# users/views.py

from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
import random
import string
from .utils import create_otp, send_welcome_email, send_password_reset_email, send_password_change_notification, send_document_rejection_email, send_document_verification_email
from django.utils import timezone
from django.db.models import Q
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

from .models import OTP, CustomUser, UserProfile
from .serializers import (
    CustomUserSerializer,
    OTPVerificationSerializer, 
    UserCreateSerializer,
    ChangePasswordSerializer,
    AdminPasswordChangeSerializer,
    UpdateUserSerializer,
    AdminUpdateUserSerializer,
    ProfileUpdateSerializer,
    DocumentVerificationSerializer,
    ProfileSerializer
)
from .permissions import IsAdminUser, IsSelfOrAdmin, CanChangeRestrictedFields

import logging
logger = logging.getLogger(__name__)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for users
    """
    queryset = CustomUser.objects.all()

    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action == 'admin_change_password':
            return AdminPasswordChangeSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            if self.request.user.user_type == 'ADMIN':
                return AdminUpdateUserSerializer
            return UpdateUserSerializer
        return CustomUserSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action in ['update', 'partial_update']:
            permission_classes = [IsAuthenticated, IsSelfOrAdmin, CanChangeRestrictedFields]
        elif self.action in ['handle_user_by_id_number', 'handle_profile_by_id_number']:
            permission_classes = [IsAuthenticated]
            if self.request.method in ['PATCH', 'PUT']:
                permission_classes.append(IsSelfOrAdmin)
        elif self.action == 'create' or self.action == 'list':
            permission_classes = [IsAdminUser]
        elif self.action == 'admin_change_password':
            permission_classes = [IsAdminUser]
        elif self.action in ['destroy']:
            permission_classes = [IsAuthenticated, IsSelfOrAdmin]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Get current user's data including profile"""
        user = request.user
        try:
            profile = user.profile
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            profile = UserProfile.objects.create(user=user)

            if request.method == 'PATCH':
                serializer = self.get_serializer(
                    request.user,
                    data=request.data,
                    partial=True
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response(serializer.data)
            
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        
        user_data = self.get_serializer(user).data
        user_data['profile'] = ProfileUpdateSerializer(profile).data
        return Response(user_data)
    
    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        try:
            user = request.user
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')

            if not old_password or not new_password:
                return Response(
                    {'error': 'Both old and new passwords are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify old password
            if not authenticate(username=user.id_number, password=old_password):
                return Response(
                    {'error': 'Current password is incorrect'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Change password
            user.set_password(new_password)
            user.is_first_login = False
            user.save()

            # Send notification email
            email_sent = send_password_change_notification(user)

            return Response({
                'status': 'success',
                'message': 'Password changed successfully',
                'email_sent': email_sent
            })

        except Exception as e:
            logger.error(f"Password change failed for user {request.user.id_number}: {str(e)}")
            return Response(
                {'error': 'Password change failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
    def admin_change_password(self, request):
        """
        Allow admin users to change any user's password
        """
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = get_object_or_404(User, id_number=serializer.validated_data.get('user_id'))
            
            # Set new password
            user.set_password(serializer.validated_data.get('new_password'))
            user.password_changed = False  # Reset so user has to change on next login
            user.save()
            
            return Response({'status': 'password changed'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='admin-reset-password')
    def admin_reset_password(self, request):
        if not request.user.user_type == 'ADMIN':
            return Response(
                {'error': 'Only administrators can reset passwords'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = request.data.get('user_id')
        new_password = request.data.get('new_password')
        send_email = request.data.get('send_email', False)

        try:
            user = self.queryset.get(id_number=user_id)
            user.set_password(new_password)
            user.is_first_login = True
            user.save()

            if send_email:
                sent = send_password_reset_email(user, new_password)
                if not sent:
                    return Response({
                        'message': 'Password reset successful but email failed to send',
                        'warning': 'Email notification failed'
                    })

            return Response({
                'message': 'Password reset successful',
                'email_sent': send_email
            })

        except self.queryset.model.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user with a random password
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the password before it's hashed
        plain_password = request.data.get('password')
        
        # Create the user
        user = serializer.save()
        
        # Send welcome email with credentials
        send_welcome_email(user, plain_password)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
    
    def perform_create(self, serializer):
        serializer.save()
    
    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            old_data = self.get_serializer(instance).data
            
            response = super().update(request, *args, **kwargs)
            
            if response.status_code in [200, 201]:
                # Compare old and new data to get changes
                new_data = response.data
                changes = {}
                
                for field in request.data.keys():
                    if old_data.get(field) != new_data.get(field):
                        changes[field] = (old_data.get(field), new_data.get(field))
                
                if changes:
                    notify_admins_of_changes(
                        admin_actor=request.user,
                        modified_user=instance,
                        changes=changes,
                        action_type='profile_update'
                    )
            
            return response
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated], url_path='request-otp')
    def request_otp(self, request):
        """Request a new OTP"""
        try:
            otp = create_otp(request.user)
            return Response(
                {'message': 'OTP sent successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            print(f"OTP Error: {str(e)}")  # For debugging
            return Response(
                {'error': 'Failed to send OTP'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def verify_otp(self, request):
        """Verify OTP code"""
        serializer = OTPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        otp_code = serializer.validated_data['otp']
        user = request.user
        
        try:
            otp = OTP.objects.get(
                user=user,
                code=otp_code,
                is_used=False
            )
            
            if not otp.is_valid():
                return Response(
                    {'error': 'OTP has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Mark OTP as used
            otp.is_used = True
            otp.save()
            
            return Response({
                'message': 'OTP verified successfully',
                'user': CustomUserSerializer(user).data
            })
            
        except OTP.DoesNotExist:
            return Response(
                {'error': 'Invalid OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='verify-login',
        url_name='verify-login'
    )
    def verify_login(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        otp_code = serializer.validated_data['otp']

        try:
            otp = OTP.objects.get(
                user=user,
                code=otp_code,
                is_used=False
            )

            if not otp.is_valid():
                return Response(
                    {'error': 'OTP has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Mark OTP as used
            otp.is_used = True
            otp.save()

            # Generate new token pair after OTP verification
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': {
                    'id_number': user.id_number,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'user_type': user.user_type,
                }
            })

        except OTP.DoesNotExist:
            return Response(
                {'error': 'Invalid OTP'},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='by-id-number/(?P<id_number>[^/.]+)',
        url_name='user-by-id'
    )
    def handle_user_by_id_number(self, request, id_number=None):
        try:
            user = self.queryset.get(id_number=id_number)
            
            if request.method == 'GET':
                serializer = self.get_serializer(user)
                return Response(serializer.data)
            
            elif request.method == 'PATCH':
                if request.user.user_type != 'ADMIN' and request.user.id_number != id_number:
                    return Response(
                        {'error': 'You do not have permission to modify this user'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                    
                serializer = self.get_serializer(
                    user,
                    data=request.data,
                    partial=True
                )
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )
                    
        except CustomUser.DoesNotExist:
            return Response(
                {'error': f'User with ID number {id_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=False,
        methods=['get', 'patch'],
        url_path='by-id-number/(?P<id_number>[^/.]+)/profile',
        url_name='profile-by-id'
    )
    def handle_profile_by_id_number(self, request, id_number=None):
        try:
            user = self.queryset.get(id_number=id_number)
            
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = UserProfile.objects.create(user=user)

            if request.method == 'GET':
                serializer = ProfileUpdateSerializer(profile)
                return Response(serializer.data)
            
            elif request.method == 'PATCH':
                serializer = ProfileUpdateSerializer(
                    profile,
                    data=request.data,
                    partial=True,
                    context={'request': request} if request.FILES else None
                )
                
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    
        except CustomUser.DoesNotExist:
            return Response(
                {'error': f'User with ID number {id_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminUser],
        url_path='unverified-documents',
        url_name='unverified-documents'
    )
    def unverified_documents(self, request):
        """Get users with unverified documents"""
        try:
            # Add debug logging
            logger.debug("Fetching unverified documents")
            
            # Modified query to check for any document that needs verification
            unverified_users = self.queryset.filter(
                profile__isnull=False  # Must have a profile
            ).filter(
                Q(profile__id_front_verified=False) |
                Q(profile__id_back_verified=False) |
                Q(profile__passport_photo_verified=False) |
                Q(profile__signature_verified=False)
            ).filter(
                # At least one document must be uploaded
                Q(profile__id_front_image__isnull=False) |
                Q(profile__id_back_image__isnull=False) |
                Q(profile__passport_photo__isnull=False) |
                Q(profile__signature__isnull=False)
            ).distinct()

            # Log the count for debugging
            logger.debug(f"Found {unverified_users.count()} users with unverified documents")
            
            serializer = CustomUserSerializer(unverified_users, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error fetching unverified documents: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=True, 
        methods=['patch'], 
        permission_classes=[IsAdminUser],
        url_path='verify-documents'
    )
    def verify_documents(self, request, pk=None):
        """Verify user documents"""
        try:
            user = self.get_object()
            profile = user.profile
            
            # Get verification data
            document_type = request.data.get('document_type')
            new_status = request.data.get('status')
            notes = request.data.get('notes', '')

            if document_type not in ['id_front', 'id_back', 'passport_photo', 'signature']:
                return Response(
                    {'error': 'Invalid document type'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update specific document verification
            verified_field = f'{document_type}_verified'
            setattr(profile, verified_field, new_status == 'VERIFIED')

            # Update verification metadata
            profile.verification_notes = notes
            if new_status == 'VERIFIED':
                profile.verified_at = timezone.now()
                profile.verified_by = request.user

            # Update overall verification status
            if profile.documents_verified:
                profile.verification_status = 'VERIFIED'
            elif new_status == 'REJECTED':
                profile.verification_status = 'REJECTED'
            else:
                profile.verification_status = 'PENDING'

            profile.save()

            serializer = ProfileSerializer(profile)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=False,
        methods=['patch'],
        permission_classes=[IsAdminUser],
        url_path='by-id-number/(?P<id_number>[^/.]+)/verify-documents',
        url_name='verify-documents-by-id'
    )
    def verify_documents_by_id(self, request, id_number=None):
        """Verify user documents by ID number"""
        try:
            user = self.queryset.get(id_number=id_number)
            profile = user.profile
            
            document_type = request.data.get('document_type')
            new_status = request.data.get('status')
            notes = request.data.get('notes', '')

            if document_type not in ['id_front', 'id_back', 'passport_photo', 'signature', 'all']:
                return Response(
                    {'error': 'Invalid document type'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update verification status
            is_approved = new_status == 'approve'
            if document_type == 'all':
                profile.id_front_verified = is_approved
                profile.id_back_verified = is_approved
                profile.passport_photo_verified = is_approved
                profile.signature_verified = is_approved
            else:
                verified_field = f'{document_type}_verified'
                setattr(profile, verified_field, is_approved)

            # Update verification metadata
            profile.verification_notes = notes
            profile.verified_at = timezone.now()
            profile.verified_by = request.user

            # Update overall verification status
            if new_status == 'approve':
                if document_type == 'all' or profile.documents_verified:
                    profile.verification_status = 'VERIFIED'
                    # Send email for all documents verified
                    try:
                        send_document_verification_email(user, document_type, all_verified=True)
                    except Exception as e:
                        logger.error(f"Failed to send verification email: {str(e)}")
                else:
                    # Send email for single document verification
                    try:
                        send_document_verification_email(user, document_type)
                    except Exception as e:
                        logger.error(f"Failed to send verification email: {str(e)}")
            elif new_status == 'reject':
                profile.verification_status = 'REJECTED'
                # Send rejection email
                try:
                    send_document_rejection_email(user, document_type, notes)
                except Exception as e:
                    logger.error(f"Failed to send rejection email: {str(e)}")
            else:
                profile.verification_status = 'PENDING'

            profile.save()

            serializer = ProfileSerializer(profile)
            return Response(serializer.data)

        except CustomUser.DoesNotExist:
            return Response(
                {'error': f'User with ID number {id_number} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Document verification error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAdminUser],
        url_path='dashboard-stats',
        url_name='dashboard-stats'
    )
    def dashboard_stats(self, request):
        """Get dashboard statistics"""
        try:
            logger.debug("Fetching dashboard stats")
            
            # Get basic stats
            members = self.queryset.filter(user_type='MEMBER')
            total_members = members.count()
            logger.debug(f"Total members: {total_members}")
            
            # Get verification stats
            verification_stats = {
                'pending': UserProfile.objects.filter(
                    Q(verification_status='PENDING') | 
                    Q(verification_status__isnull=True)
                ).count(),
                'verified': UserProfile.objects.filter(
                    verification_status='VERIFIED'
                ).count(),
                'rejected': UserProfile.objects.filter(
                    verification_status='REJECTED'
                ).count()
            }
            logger.debug(f"Verification stats: {verification_stats}")

            # Get recent members with profiles
            recent_members = members.select_related('profile').order_by(
                '-date_joined'
            )[:5].values(
                'id_number',
                'first_name',
                'last_name',
                'email',
                'date_joined',
                'profile__verification_status'
            )
            logger.debug(f"Recent members count: {len(recent_members)}")

            stats = {
                'total_members': total_members,
                'pending_verifications': verification_stats['pending'],
                'active_loans': 0,  # Placeholder for future loan functionality
                'recent_members': list(recent_members),
                'verification_stats': verification_stats
            }
            logger.debug("Successfully compiled dashboard stats")

            return Response(stats)
            
        except Exception as e:
            logger.error(f"Error fetching dashboard stats: {str(e)}")
            return Response(
                {'error': f'Failed to fetch dashboard statistics: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProfileViewSet(mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin,
                     viewsets.GenericViewSet):
    """
    API endpoint for user profiles
    """
    queryset = UserProfile.objects.all()
    
    def get_serializer_class(self):
        if self.action == 'verify_documents' and self.request.user.user_type == 'ADMIN':
            return DocumentVerificationSerializer
        return ProfileUpdateSerializer
    
    def get_permissions(self):
        if self.action == 'verify_documents':
            permission_classes = [IsAdminUser]
        else:
            permission_classes = [IsAuthenticated, IsSelfOrAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=False, methods=['get', 'put', 'patch'])
    def me(self, request):
        """
        Get or update the user's own profile
        """
        profile = request.user.profile
        
        if request.method in ['PUT', 'PATCH']:
            serializer = self.get_serializer(profile, data=request.data, partial=request.method=='PATCH')
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def verify_documents(self, request, pk=None):
        """
        Allow admin to verify user documents
        """
        profile = self.get_object()
        serializer = DocumentVerificationSerializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'Document verification status updated',
                'verified': profile.documents_verified
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Get the user
        user = self.user
        
        # Generate OTP and send email
        otp = create_otp(user)
        
        # Add custom claims
        data['user'] = {
            'id_number': user.id_number,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type,
        }
        
        return data

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer