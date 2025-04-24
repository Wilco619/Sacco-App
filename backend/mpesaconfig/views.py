# views.py
import requests, base64, json, re, os
from datetime import datetime, timezone
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Transaction
from finance.models import Member, MembershipFee, Share, Profit, FinancialPeriod
from .serializers import TransactionSerializer, PaymentSerializer, STKQuerySerializer
from dotenv import load_dotenv
from django.db import transaction
from accounts.models import ShareCapital
from decimal import Decimal
from .registration_payments import RegistrationPaymentHandler
from .share_payments import SharePaymentHandler
from .handlers.factory import PaymentHandlerFactory

import logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Retrieve variables from the environment
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
CALLBACK_URL = os.getenv("MPESA_CALLBACK_BASE_URL")
MPESA_BASE_URL = os.getenv("MPESA_BASE_URL")

class MPesaViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action == 'callback':
            permission_classes = []
        else:
            permission_classes = [IsAuthenticated]  # Or whatever permissions you normally use
        return [permission() for permission in permission_classes]

    # Phone number formatting and validation
    def format_phone_number(self, phone):
        phone = phone.replace("+", "")
        if re.match(r"^254\d{9}$", phone):
            return phone
        elif phone.startswith("0") and len(phone) == 10:
            return "254" + phone[1:]
        else:
            raise ValueError("Invalid phone number format")

    # Generate M-Pesa access token
    def generate_access_token(self):
        try:
            credentials = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
            }
            response = requests.get(
                f"{MPESA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
                headers=headers,
            ).json()

            if "access_token" in response:
                return response["access_token"]
            else:
                raise Exception("Access token missing in response.")

        except requests.RequestException as e:
            raise Exception(f"Failed to connect to M-Pesa: {str(e)}")

    # Initiate STK Push and handle response
    def trigger_stk_push(self, phone, amount, description="Payment for goods"):
        try:
            token = self.generate_access_token()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            stk_password = base64.b64encode(
                (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
            ).decode()

            request_body = {
                "BusinessShortCode": MPESA_SHORTCODE,
                "Password": stk_password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": float(amount),  # Convert Decimal to float
                "PartyA": phone,
                "PartyB": MPESA_SHORTCODE,
                "PhoneNumber": phone,
                "CallBackURL": CALLBACK_URL,
                "AccountReference": "account",
                "TransactionDesc": description,
            }

            response = requests.post(
                f"{MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest",
                json=request_body,
                headers=headers,
            ).json()

            return response

        except Exception as e:
            print(f"Failed to initiate STK Push: {str(e)}")
            return {"error": str(e)}

    # Query STK Push status
    def query_stk_push(self, checkout_request_id):
        """Query STK push status from M-Pesa"""
        try:
            token = self.generate_access_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                (MPESA_SHORTCODE + MPESA_PASSKEY + timestamp).encode()
            ).decode()

            request_body = {
                "BusinessShortCode": MPESA_SHORTCODE,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }

            logger.info(f"STK Query Request for {checkout_request_id}: {request_body}")
            
            response = requests.post(
                f"{MPESA_BASE_URL}/mpesa/stkpushquery/v1/query",
                json=request_body,
                headers=headers,
            )
            
            # Log raw response
            logger.info(f"STK Raw Response: {response.text}")
            
            response_data = response.json()
            
            # Return structured response
            return {
                'ResultCode': response_data.get('ResultCode', 'None'),
                'ResultDesc': response_data.get('ResultDesc', 'Query in progress'),
                'ResponseCode': response_data.get('ResponseCode', 'None'),
                'ResponseDesc': response_data.get('ResponseDescription'),
                'MerchantRequestID': response_data.get('MerchantRequestID'),
                'CheckoutRequestID': response_data.get('CheckoutRequestID'),
                'ResultParameters': response_data.get('ResultParameters', {})
            }

        except requests.RequestException as e:
            logger.error(f"STK query failed: {str(e)}")
            return {
                'ResultCode': 'Error',
                'ResultDesc': str(e),
                'ResponseCode': 'Error'
            }

    @action(detail=False, methods=['post'])
    def initiate_payment(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                phone = self.format_phone_number(serializer.validated_data["phone_number"])
                amount = serializer.validated_data["amount"]
                payment_type = serializer.validated_data.get("payment_type", "REGISTRATION")

                # Changed from initiate_stk_push to trigger_stk_push
                response = self.trigger_stk_push(
                    phone, 
                    amount,
                    f"{payment_type} Payment"  # Add payment type to description
                )

                if response.get("ResponseCode") == "0":
                    # Create transaction record
                    transaction = Transaction.objects.create(
                        user=request.user,
                        payment_type=payment_type,
                        amount=amount,
                        phone_number=phone,
                        checkout_request_id=response["CheckoutRequestID"],
                        merchant_request_id=response.get("MerchantRequestID"),
                        status='PENDING'
                    )

                    return Response({
                        "success": True,
                        "message": "STK push initiated successfully",
                        "checkout_request_id": response["CheckoutRequestID"],
                        "transaction_id": transaction.id
                    }, status=status.HTTP_200_OK)
                else:
                    error_message = response.get("errorMessage", "Failed to send STK push")
                    return Response({
                        "success": False,
                        "message": error_message
                    }, status=status.HTTP_400_BAD_REQUEST)

            except ValueError as e:
                return Response({
                    "success": False,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Payment initiation error: {str(e)}")
                return Response({
                    "success": False,
                    "message": f"An unexpected error occurred: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def query_status(self, request):
        try:
            checkout_request_id = request.data.get('checkout_request_id')
            if not checkout_request_id:
                return Response({
                    'success': False,
                    'message': 'Checkout request ID is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get transaction from database
            transaction = Transaction.objects.select_related('user').get(
                checkout_request_id=checkout_request_id
            )

            # Query M-Pesa status
            stk_status = self.query_stk_push(checkout_request_id)
            logger.info(f"STK query response for {checkout_request_id}: {stk_status}")

            if stk_status.get('ResultCode') == '0':
                # Update transaction status
                transaction.status = 'COMPLETED'
                transaction.result_code = stk_status.get('ResultCode')
                transaction.result_description = stk_status.get('ResultDesc')
                transaction.save()

                # Process the payment using appropriate handler
                try:
                    handler = PaymentHandlerFactory.get_handler(transaction.payment_type)
                    handler_response = handler.process_payment(mpesa_transaction=transaction)
                    
                    logger.info(f"Payment processed successfully: {handler_response}")

                    return Response({
                        'success': True,
                        'status': {
                            'ResultCode': stk_status.get('ResultCode'),
                            'ResultDesc': stk_status.get('ResultDesc'),
                            'ResponseCode': stk_status.get('ResponseCode'),
                            'ResponseDesc': stk_status.get('ResponseDescription'),
                            'TransactionStatus': transaction.status,
                            'MpesaReceiptNumber': transaction.mpesa_code,
                            'Amount': str(transaction.amount),
                            'CheckoutRequestID': checkout_request_id,
                            'PaymentType': transaction.payment_type,
                            'PaymentDetails': handler_response
                        }
                    })

                except Exception as e:
                    logger.error(f"Payment processing error: {str(e)}", exc_info=True)
                    transaction.status = 'PROCESSING_FAILED'
                    transaction.save()
                    raise

            # Return current status if not successful
            return Response({
                'success': True,
                'status': {
                    'ResultCode': stk_status.get('ResultCode'),
                    'ResultDesc': stk_status.get('ResultDesc'),
                    'ResponseCode': stk_status.get('ResponseCode'),
                    'ResponseDesc': stk_status.get('ResponseDescription'),
                    'TransactionStatus': transaction.status,
                    'MpesaReceiptNumber': transaction.mpesa_code,
                    'Amount': str(transaction.amount),
                    'CheckoutRequestID': checkout_request_id,
                    'PaymentType': transaction.payment_type
                }
            })

        except Transaction.DoesNotExist:
            logger.error(f"Transaction not found for checkout_request_id: {checkout_request_id}")
            return Response({
                'success': False,
                'message': 'Transaction not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Status query error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': f'Failed to query payment status: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    @csrf_exempt
    def callback(self, request):
        """Handle M-Pesa callback"""
        try:
            logger.info("Raw callback data received: %s", request.body.decode('utf-8'))
            
            callback_data = request.data.get("Body", {}).get("stkCallback", {})
            checkout_request_id = callback_data.get("CheckoutRequestID")
            result_code = callback_data.get("ResultCode")
            result_desc = callback_data.get("ResultDesc", "")
            
            logger.info(f"Processing callback for checkout_request_id: {checkout_request_id}")
            logger.info(f"Result code: {result_code}, Description: {result_desc}")
            
            try:
                transaction = Transaction.objects.select_related('user').get(
                    checkout_request_id=checkout_request_id
                )
            except Transaction.DoesNotExist:
                logger.error(f"Transaction not found for checkout_request_id: {checkout_request_id}")
                return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

            if result_code == 0:  # Successful transaction
                try:
                    metadata = callback_data.get("CallbackMetadata", {}).get("Item", [])
                    metadata_dict = {item["Name"]: item["Value"] for item in metadata}

                    # Update transaction details
                    transaction.mpesa_code = metadata_dict.get("MpesaReceiptNumber")
                    transaction.amount = metadata_dict.get("Amount", transaction.amount)
                    transaction.phone_number = metadata_dict.get("PhoneNumber", transaction.phone_number)
                    transaction.status = 'COMPLETED'
                    transaction.save()

                    logger.info(f"Processing {transaction.payment_type} payment for user {transaction.user.id}")

                    # Get appropriate handler and process payment
                    handler = PaymentHandlerFactory.get_handler(transaction.payment_type)
                    if handler:
                        try:
                            handler_response = handler.process_payment(
                                mpesa_transaction=transaction
                            )
                            logger.info(f"Payment processed successfully: {handler_response}")
                            
                            # Return success response with handler data
                            return Response({
                                "ResultCode": 0,
                                "ResultDesc": "Payment processed successfully",
                                "Data": handler_response
                            })
                        except Exception as handler_error:
                            logger.error(f"Handler error: {str(handler_error)}", exc_info=True)
                            transaction.status = 'HANDLER_FAILED'
                            transaction.save()
                            raise
                    else:
                        logger.error(f"No handler found for payment type: {transaction.payment_type}")
                        transaction.status = 'HANDLER_NOT_FOUND'
                        transaction.save()
                        raise ValueError(f"No handler found for payment type: {transaction.payment_type}")

                except Exception as e:
                    logger.error(f"Error processing payment: {str(e)}", exc_info=True)
                    transaction.status = 'FAILED'
                    transaction.save()
                    raise

            # Payment failed
            transaction.status = 'FAILED'
            transaction.result_description = result_desc
            transaction.save()
            
            return Response({
                "ResultCode": result_code,
                "ResultDesc": result_desc or "Payment failed"
            })

        except Exception as e:
            logger.error(f"Callback processing error: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Invalid request data: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'])
    def initiate_share_purchase(self, request):
        """Dedicated endpoint for share purchases"""
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            try:
                amount = serializer.validated_data['amount']
                phone_number = serializer.validated_data['phone_number']
                
                # Validate amount is in thousands
                if amount % 1000 != 0:
                    return Response({
                        'success': False,
                        'message': 'Share amount must be in multiples of 1000'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Format phone number
                try:
                    formatted_phone = self.format_phone_number(phone_number)
                except ValueError as e:
                    return Response({
                        'success': False,
                        'message': str(e)
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create shares transaction record
                transaction = Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    phone_number=formatted_phone,
                    payment_type='SHARES',
                    status='PENDING'
                )

                # Call STK push
                response = self.trigger_stk_push(
                    formatted_phone, 
                    amount,
                    'Share Purchase'  # Add description
                )
                
                if response.get('ResponseCode') == '0':
                    transaction.checkout_request_id = response.get('CheckoutRequestID')
                    transaction.merchant_request_id = response.get('MerchantRequestID')
                    transaction.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Share purchase initiated',
                        'checkout_request_id': response.get('CheckoutRequestID')
                    })
                
                transaction.status = 'FAILED'
                transaction.result_description = response.get('errorMessage', 'STK push failed')
                transaction.save()
                
                return Response({
                    'success': False,
                    'message': response.get('errorMessage', 'Failed to initiate payment')
                }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                logger.error(f"Share purchase error: {str(e)}")
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
