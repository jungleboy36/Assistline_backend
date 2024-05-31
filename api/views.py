from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .serializers import *
from firebase_admin import firestore, auth
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from firebase_admin import auth
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
import base64
from django.core.files.base import ContentFile
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework_jwt.settings import api_settings
from rest_framework.permissions import IsAuthenticated
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .models import Notification
from functools import wraps
from django.views.decorators.csrf import csrf_exempt
import json
from google.cloud.firestore_v1.base_query import FieldFilter
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder
import paypalrestsdk
from pusher import Pusher



def requires_role(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            user_auth, role = authenticate(request)
            if not user_auth or role not in allowed_roles:
                return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator

import base64

pusher = Pusher(
                app_id = "1801083",
                key = "1c26d2cd463b15a19666",
                secret = "e4e61f70e4b17c1a7de8",
                cluster = "eu",
                ssl=True,
                )



def authenticate(request):
    try:
        authorization_header = request.headers.get('Authorization')
        if authorization_header and authorization_header.startswith('Bearer '):
            # Extract the token from the Authorization header
            id_token_encoded = authorization_header[len('Bearer '):]
            
            # Decode the Base64-encoded token
            id_token_decoded = base64.b64decode(id_token_encoded).decode('utf-8')
            
            # Verify the decoded token with Firebase Authentication
            decoded_token = auth.verify_id_token(id_token_decoded)
            #print('Decoded token : ', decoded_token)
            
            user_id = decoded_token['uid']
            role = firestore.client().collection('users').document(user_id).get().to_dict()
            role = role['role']
            print('Role : ', role)
            
            return user_id, role
    except Exception as e:
        print(f"Error verifying token in authorization header: {e}")
        pass  # Continue checking for token in other sources
    
    # No valid token found
    return None, None  # Or return an error response indicating missing token


class OffresViewSet(viewsets.ViewSet):
        # Check if user_id is provided in the query parameters
    def list(self, request):
        #user_auth, role = authenticate(request)
        # Check if user_id is provided in the query parameters
        #if user_auth and role == 'client'or role =='company':
            user_id = request.query_params.get('user_id')
            if user_id:
                # If user_id is provided, filter offers by user_id
                offres = firestore.client().collection('offres').where('user_id', '==', user_id).get()
            else:
                # If user_id is not provided, list all offers
                offres = firestore.client().collection('offres').get()
            
            data = []
            user =[]
            for doc in offres:
                offer_data = doc.to_dict()
                user_id = offer_data.get('user_id')
                # Fetch user information based on user_id
                if user_id is not None:
                    user = firestore.client().collection('users').document(user_id).get().to_dict()
                    # Add user information to offer data
                    offer_data['username'] = user['name']
                    offer_data['picture'] = user['image']
                
                data.append({'id': doc.id, **offer_data})
            return Response(data)

    @requires_role(['company'])
    def create(self, request):
        serializer = OffresSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['creationDate'] = timezone.now()
            firestore.client().collection('offres').add(data)
            notification_message = f'Nouvelle offre ajouté: {data["title"]}'
                # Save the notification to the 'notifications' collection in Firestore
            notification_data = {
                      # Replace with admin user ID
                    'message': notification_message,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                }
            notification_ref = firestore.client().collection('notifications').add(notification_data)
            notification_id = notification_ref[1].id
            
            # Update users with role 'client' to add the notification ID to their notifications array
            clients = firestore.client().collection('users').where('role', '==', 'client').get()
            for client in clients:
                client_ref = firestore.client().collection('users').document(client.id)
                client_ref.update({'notifications': firestore.ArrayUnion([notification_id])})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @requires_role(['company'])
    def update(self, request, pk=None):
        serializer = OffresSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['updateDate'] = timezone.now()
            firestore.client().collection('offres').document(pk).set(data, merge=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @requires_role(['company'])
    def partial_update(self, request, pk=None):
        return self.update(request, pk)
    @requires_role(['company'])
    def destroy(self, request, pk=None):
        firestore.client().collection('offres').document(pk).delete()
        return Response(status=status.HTTP_200_OK)
    def retrieve(self, request, pk=None):
        offre = firestore.client().collection('offres').document(pk).get()
        if offre.exists:
            data = offre.to_dict()
            user = firestore.client().collection('users').document(data.get('user_id')).get().to_dict()
            data['username'] = user['name']
            return Response(data,status=status.HTTP_200_OK)
        return Response({'error': 'Demand not found'}, status=status.HTTP_404_NOT_FOUND)



class DemandesViewSet(viewsets.ViewSet):
    serializer_class = DemandesSerializer
    @requires_role(['client', 'company'])
    def list(self, request):
        user_id = request.query_params.get('user_id')
        if user_id:
            # If user_id is provided, filter offers by user_id
            demandes = firestore.client().collection('demandes').where('user_id', '==', user_id).get()
        else:
            # If user_id is not provided, list all offers
            demandes = firestore.client().collection('demandes').get()

        data = []
        user =[]
        for doc in demandes:
            demande_data = doc.to_dict()
            user_id = demande_data.get('user_id')
            # Fetch user information based on user_id
            if user_id is not None:
                print('*********user id: ',user_id)

                user = firestore.client().collection('users').document(user_id).get().to_dict()
                # Add user information to demande data
                demande_data['username'] = user['name']
                demande_data['picture'] = user['image']
            
            data.append({'id': doc.id, **demande_data})
        return Response(data)
    @requires_role(['client'])
    def create(self, request):
        serializer = DemandesSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            data['creationDate'] = timezone.now()
            firestore.client().collection('demandes').add(data)
            notification_message = f'Nouvelle demande ajouté: {data["title"]}'
                # Save the notification to the 'notifications' collection in Firestore
            notification_data = {
                      # Replace with admin user ID
                    'message': notification_message,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                   
                }
            notification_ref =  db.collection('notifications').add(notification_data)
            notification_id = notification_ref[1].id
            
            # Update users with role 'client' to add the notification ID to their notifications array
            companies = firestore.client().collection('users').where('role', '==', 'company').get()
            for company in companies:
                company_ref = firestore.client().collection('users').document(company.id)
                company_ref.update({'notifications': firestore.ArrayUnion([notification_id])})
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @requires_role(['client', 'company'])
    def retrieve(self, request, pk=None):
        offre = firestore.client().collection('demandes').document(pk).get()
        if offre.exists:
            data = offre.to_dict()
            user = firestore.client().collection('users').document(data.get('user_id')).get().to_dict()
            data['username'] = user['name']
            return Response(data,status=status.HTTP_200_OK)
        return Response({'error': 'Demand not found'}, status=status.HTTP_404_NOT_FOUND)
    @requires_role(['client'])
    def update(self, request, pk=None):
        serializer = DemandesSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['updateDate'] = timezone.now()
            firestore.client().collection('demandes').document(pk).set(data,merge= True)
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @requires_role(['client'])
    def partial_update(self, request, pk=None):
        return self.update(request, pk)
    @requires_role(['client'])
    def destroy(self, request, pk=None):
        firestore.client().collection('demandes').document(pk).delete()
        return Response(status=status.HTTP_200_OK)


class RegisterViewSet(viewsets.ViewSet):
    def create(self, request, *args, **kwargs):
        role = request.data.get('role')
        serializer = UserSerializer(data=request.data)

        if serializer.is_valid():
            # Save the user data in the Django database
            instance = serializer.save()

            # Retrieve the data from the serializer
            data = serializer.data
            user_data = {
                'email': data['email'],
                'password': data['password']
            }

            try:
                # Create the user in Firebase Authentication without the name initially
                firebase_user = auth.create_user(**user_data)

                # Now, update the user's display name separately
                auth.update_user(firebase_user.uid, display_name=data['name'])
                link = auth.generate_email_verification_link(data['email'], action_code_settings=None)
                send_verification_email('achrafhafsia9@gmail.com',link,data['role'])
                # Create a Firestore client
                db = firestore.client()

                # Use the Firebase Authentication user ID (uid) as the document ID
                uid = firebase_user.uid

                # Add other user details to the `user_data` dictionary
                user_data.update({
                    'name': data['name'],
                    'role': data['role'],
                    'phone': data.get('phone'),
                    'dateInscription': data['dateInscription'],
                    'bio': data.get('bio'),
                    'city': data.get('city'),
                    'image': data.get('image')
                })
                user_data.pop('password')
                # Include the Base64 encoded file in the user data if provided
                if 'file' in data:
                    user_data['file'] = data['file']
                if data['role'] == 'company' :
                    user_data['enabled'] = False
                else :
                    user_data['enabled'] = True
                # Save the user data in Firestore under the 'users' collection with the user's UID as the document ID
                db.collection('users').document(uid).set(user_data)
                
                # Return a successful response with the serialized data and a status code of 201_CREATED
            
                notification_message = f'New {role} registered: {data["name"]}'
                # Save the notification to the 'notifications' collection in Firestore
                notification_data = {
                      # Replace with admin user ID
                    'message': notification_message,
                    'timestamp': firestore.SERVER_TIMESTAMP,
                    
                }

                notification_ref = db.collection('notifications').add(notification_data)
                
                # Retrieve the ID of the notification
                notification_id = notification_ref.id
                
                # Update the user's document to include the notification ID
                db.collection('users').document('pcVxTGFxIxN6ejqR7mLHSQnUFhZ2').update({
                    'notification_id': notification_id
                })
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            except Exception as e:
                # Handle any errors that occur during user creation in Firebase
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # If the data is invalid, return the serializer errors and a status code of 400_BAD_REQUEST
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


jwt_settings = api_settings.JWT_ENCODE_HANDLER

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                # Retrieve the user by email
                user = auth.get_user_by_email(email)

                # Check if the user exists
                if not user:
                    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

                # Create a Firestore client
                db = firestore.client()
                # Retrieve the user's document in Firestore using the user's UID
                user_doc = db.collection('users').document(user.uid).get()
                id_token = firebase_authenticate(email, password)

                # Verify if the user's account is enabled
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    role = user_data.get('role')
                    if not user_data.get('enabled', True):
                        return Response({'error': 'Account disabled'}, status=status.HTTP_403_FORBIDDEN)

                # Generate a JWT token containing user info and role
                payload = {
                    'uid': user.uid,
                    'email': user.email,
                    'role': role,
                    'display_name': user.display_name,
                    # Add other user attributes as needed
                }
                token = jwt_settings(payload)
                print("*********** authenticated : "+ id_token)
                if(is_user_verified(user.uid) and id_token):
                    return Response({
                        'message': 'Login successful',
                        'token': token
                    }, status=status.HTTP_200_OK)
                elif(id_token) :
                    return
                elif(not is_user_verified(user.uid)) :
                    return Response({'error': 'Email unverified'}, status=status.HTTP_403_FORBIDDEN)
                elif (error_message):
                    return Response({'error': 'Email ou mot de passe erroné'}, status=status.HTTP_403_FORBIDDEN)

            except Exception as e:
                # Handle any authentication errors
                return Response({'error': 'Login failed', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Return serializer errors
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    def get(self, request):
        # Get the UID from the request's query parameters
        uid = request.GET.get('uid')
        
        # Create a Firestore client
        db = firestore.client()
        
        # Access the 'users' collection and retrieve the document with the provided UID
        user_doc_ref = db.collection('users').document(uid)
        user_doc = user_doc_ref.get()

        # Check if the document exists
        if not user_doc.exists:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Retrieve user data from the document
        user_data = user_doc.to_dict()
        
        # Return the user data as a response
        return Response(user_data, status=status.HTTP_200_OK)

    def put(self, request):
        uid = request.GET.get('uid')
        
        # Create Firestore client
        db = firestore.client()
        user_doc_ref = db.collection('users').document(uid)
        user_doc = user_doc_ref.get()

        # Check if the user document exists
        if not user_doc.exists:
            return JsonResponse({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        updated_data = request.data
        
        # Only update the allowed fields in Firestore
        allowed_fields = ['name', 'phone', 'bio', 'city', 'image', 'role','hideEmail','paypalEmail']
        filtered_data = {field: updated_data[field] for field in allowed_fields if field in updated_data}

        # Update Firestore document
        user_doc_ref.update(filtered_data)
        
        # Return success response
        return JsonResponse({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)




class AdminCompaniesViewSet(viewsets.ViewSet):
    @requires_role(['admin'])
    def list(self, request):
        # List all companies (users with 'company' role)
        db = firestore.client()
        users_ref = db.collection('users').where('role', '==', 'company')
        companies = users_ref.stream()

        company_list = []
        for company in companies:
            if(is_user_verified(company.id)):
                company_data = company.to_dict()
                company_data['uid'] = company.id
                company_list.append(company_data)

        return Response(company_list, status=status.HTTP_200_OK)
    @requires_role(['admin'])
    def update(self, request, pk=None):
        # Update the user's account enabled/disabled status
        enabled = request.data.get('enabled')
        if enabled is None:
            return Response({'error': 'Missing "enabled" parameter'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the user's 'enabled' field in Firestore
        db = firestore.client()
        user_doc = db.collection('users').document(pk)
        user_doc.update({'enabled': enabled})
        user = db.collection('users').document(pk).get().to_dict()
        print(user['email'])
        username = user['name']
        if enabled :
            send_email('achrafhafsia9@gmail.com',f'Bonjour {username},\nnous vous informons que votre compte a été désactivé.')

        else :
            send_email('achrafhafsia9@gmail.com',f'Bonjour {username},\nnous vous informons que votre compte a été activé.')


        # Return a successful response
        return Response({'message': 'User account updated successfully'}, status=status.HTTP_200_OK)
    @requires_role(['admin'])
    def retrieve(self, request, pk=None):
        # Retrieve user details and file URL
        db = firestore.client()
        user_doc = db.collection('users').document(pk).get()

        if not user_doc.exists:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user_data = user_doc.to_dict()

        # Return the user data
        return Response(user_data, status=status.HTTP_200_OK)

@api_view(['GET'])
def download_file(request, pk=None):
    
        # Retrieve the user's file URL and download the file
        db = firestore.client()
        user_doc = db.collection('users').document(pk).get()

        if not user_doc.exists:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user_data = user_doc.to_dict()
        file_url = user_data.get('file')

        if not file_url:
            return Response({'error': 'No file available'}, status=status.HTTP_404_NOT_FOUND)

        # Download and return the file
        # Implement the logic to download the file using file_url and send it as a response

        return Response({'file_url': file_url}, status=status.HTTP_200_OK)

@api_view(['GET'])
def check_status(request, pk=None):
        db = firestore.client()
        user_doc = db.collection('users').document(pk).get()

        if not user_doc.exists:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user_data = user_doc.to_dict()
        enabled = user_data.get('enabled')

        if enabled is None:
            return Response({'error': 'No enabled status available'}, status=status.HTTP_404_NOT_FOUND)

        # Download and return the file
        # Implement the logic to download the file using file_url and send it as a response

        return Response({'enabled': enabled}, status=status.HTTP_200_OK)

class AdminClientsViewSet(viewsets.ViewSet):
    @requires_role(['admin'])
    def list(self, request):
        # List all companies (users with 'company' role)
        db = firestore.client()
        users_ref = db.collection('users').where('role', '==', 'client')
        clients = users_ref.stream()

        client_list = []
        for client in clients:
            if(is_user_verified(client.id)):
                client_data = client.to_dict()
                client_data['uid'] = client.id
                client_list.append(client_data)

        return Response(client_list, status=status.HTTP_200_OK)
    @requires_role(['admin'])
    def update(self, request, pk=None):
        # Update the user's account enabled/disabled status
        enabled = request.data.get('enabled')
        if enabled is None:
            return Response({'error': 'Missing "enabled" parameter'}, status=status.HTTP_400_BAD_REQUEST)

        # Update the user's 'enabled' field in Firestore
        db = firestore.client()
        user_doc = db.collection('users').document(pk)
        user_doc.update({'enabled': enabled})
        user = db.collection('users').document(pk).get().to_dict()
        print(user['email'])
        username = user["name"]
        if enabled :
            send_email('achrafhafsia9@gmail.com',f'Bonjour {username}, nous vous informons que votre compte a été désactivé.')

        else :
            send_email('achrafhafsia9@gmail.com',f'Bonjour {username}, nous vous informons que votre compte a été activé.')

        # Return a successful response
        return Response({'message': 'User account updated successfully'}, status=status.HTTP_200_OK)
    @requires_role(['admin'])
    def retrieve(self, request, pk=None):
        # Retrieve user details and file URL
        db = firestore.client()
        user_doc = db.collection('users').document(pk).get()

        if not user_doc.exists:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user_data = user_doc.to_dict()

        # Return the user data
        return Response(user_data, status=status.HTTP_200_OK)


def send_verification_email(receiver_email, verification_link,role):
    # Set up the SMTP server
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # For TLS

    # Your Gmail credentials
    gmail_sender_email = 'achrafhafsia36@gmail.com'
    gmail_app_password = 'zuhm ourh kjug jnkk'

    # Create a message
    message = MIMEMultipart()
    message['From'] = gmail_sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Email Verification'

    # Add body to email
    if role =='client':
        body = f'Click the following link to verify your email: {verification_link}'
    elif role == 'company':
        body = f'Click the following link to verify your email: {verification_link} After Confirmation you will have to wait until the admin activates your account after verifying the uploaded files'

    message.attach(MIMEText(body, 'plain'))

    # Create SMTP session
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Enable TLS
        server.login(gmail_sender_email, gmail_app_password)
        server.sendmail(gmail_sender_email, receiver_email, message.as_string())

#send_verification_email('achrafhafsia9@gmail.com','test')


def send_email(receiver_email, body):
    # Set up the SMTP server
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587  # For TLS

    # Your Gmail credentials
    gmail_sender_email = 'achrafhafsia36@gmail.com'
    gmail_app_password = 'zuhm ourh kjug jnkk'

    # Create a message
    message = MIMEMultipart()
    message['From'] = gmail_sender_email
    message['To'] = receiver_email
    message['Subject'] = 'Assistline'

    # Add body to email
    message.attach(MIMEText(body, 'plain'))

    # Create SMTP session
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Enable TLS
        server.login(gmail_sender_email, gmail_app_password)
        server.sendmail(gmail_sender_email, receiver_email, message.as_string())




def is_user_verified(user_id):
    try:
        # Retrieve user information
        user = auth.get_user(user_id)
        
        # Check if the user's email is verified
        if user.email_verified:
            return True
        else:
            return False
    except auth.UserNotFoundError:
        # Handle case where user does not exist
        return False
    except Exception as e:
        # Handle other errors
        print("Error:", e)
        return False



class GetRoleFromToken(APIView):
    def get(self, request, id_token):
        if not id_token:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user = auth.get_user_by_email(id_token)
        print('user:',user.uid)
        user_doc = firestore.client().collection('users').document(user.uid).get().to_dict()

        role = user_doc['role']
        if not role:
            return Response({'error': 'Role not found for user'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'role': role}, status=status.HTTP_200_OK)



db = firestore.client()

            # Count the number of documents in the 'users' collection with role 'client'
#client_count = len(list(db.collection('users').where('role', '==', 'client').where('enabled', '==', True).stream()))

            # Count the number of documents in the 'users' collection with role 'company'
#company_count = len(list(db.collection('users').where('role', '==', 'company').where('enabled', '==', True).stream()))

            # Count the number of documents in the 'offres' collection
#offres_count = len(list(db.collection('offres').stream()))

            # Count the number of documents in the 'demandes' collection
#demandes_count = len(list(db.collection('demandes').stream()))


class DocumentCountAPIView(APIView):
    def get(self, request):
        try:
            # Initialize Firestore client


            # Return the counts as a JSON response
            return Response({
                'client_count': client_count,
                'company_count': company_count,
                'offres_count': offres_count,
                'demandes_count': demandes_count
            })
        except Exception as e:
            # Handle any exceptions
            return Response({'error': str(e)}, status=500)



class NotificationsAPIView(APIView):
    def get(self, request):
        # Get the user ID from the request (assuming it's passed as a query parameter)
        user_id = request.GET.get('user_id')

        if not user_id:
            return JsonResponse({'error': 'User ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

        # Create a Firestore client
        db = firestore.client()

        try:
            # Retrieve the user's document
            user_doc_ref = db.collection('users').document(user_id)
            user_doc = user_doc_ref.get()

            if not user_doc.exists:
                return JsonResponse({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            # Get the list of notification IDs from the user's document
            notification_ids = user_doc.to_dict().get('notifications', [])

            if not notification_ids:
                return JsonResponse([], status=status.HTTP_200_OK, safe=False)

            # Retrieve notification details for each ID
            notifications = []
            for notification_id in notification_ids:
                notification_ref = db.collection('notifications').document(notification_id)
                notification_doc = notification_ref.get()

                if notification_doc.exists:
                    notification_data = notification_doc.to_dict()
                    notifications.append(notification_data)

            return JsonResponse(notifications, status=status.HTTP_200_OK, safe=False)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
def mark_all_as_read(request):
    # Get user ID from the request (assuming it's passed somehow)
    user_id = request.GET.get('user_id')

    if not user_id:
        return JsonResponse({'error': 'User ID not provided'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Initialize Firestore database
        db = firestore.client()

        # Update the user document to empty the notifications array
        user_ref = db.collection('users').document(user_id)
        user_ref.update({'notifications': []})

        return JsonResponse({'message': 'Notifications marked as read and cleared'}, status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
db = firestore.client()

@api_view(['GET'])
def get_conversations(request, user_id):
    try:
        conversations_ref = db.collection('conversations').where('participants', 'array_contains', user_id)
        conversations = [conv.to_dict() for conv in conversations_ref.stream()]

        # Sort conversations based on the timestamp field in descending order
        sorted_conversations = sorted(conversations, key=lambda x: x.get('timestamp', 0), reverse=True)

        return JsonResponse(sorted_conversations, safe=False)
    except Exception as e:
        # Log or return the error message
        return JsonResponse({'error': str(e)}, status=500)

from operator import itemgetter

@api_view(['GET'])
def get_messages(request, conversation_id):
    # Fetch messages for a specific conversation from Firebase Firestore
    messages_ref = db.collection('messages').where(filter=FieldFilter('id','==',conversation_id))
    messages = [msg.to_dict() for msg in messages_ref.stream()]
    messages = sorted(messages, key=itemgetter('time'))
    return JsonResponse(messages, safe=False)

@api_view(['POST'])
def create_message(request):
    if request.method == 'POST':
        # Extract message data from request
        data = request.data.copy()
        data["time"] = timezone.now()
        if not data.get("id") :
            conversation_data = {
                'participants' : [data.get("sender_id"),data.get("receiver_id")],
                'display_names': [data.get("sender_display_name"),data.get("receiver_display_name")],
                'last_message' : data.get("message"),
                'time' : timezone.now()
            }
            conversation_ref =  db.collection('conversations').add(conversation_data)
            conversation_id = conversation_ref[1].id
            conversation_ref = db.collection('conversations').document(conversation_id)
            conversation_ref.update({'id':conversation_id})
            data["id"] = conversation_id
        else :
            conversation_data = {
                'last_message' : data.get("message"),
                'time' : timezone.now()
            }
            doc_ref = db.collection("conversations").document(data.get('id'))
            doc_ref.update(conversation_data)

        message = {
            "sender_id": data.get("sender_id"),
            "message": data.get("message"),
            "time" : timezone.now(),
            "display_name": data.get("display_name"),
            "id" : data.get("id")
        }

        # Create a new message object in Firebase Firestore
        messages_ref = db.collection('messages')
        debug = db.collection('messages').where("id", "==", data.get("id")).stream()
        x = len(list(debug))
        print("**** messages: ", x)
        print("Comparison result:", x == 0)

        msg = db.collection('users').document(data.get('sender_id')).get().to_dict()
        send = False
        if (x == 0) and msg['role'] == "company" and 'autoMessage' in msg and msg.get('autoMessage') != '':
            auto_message = {
            "sender_id": data.get("receiver_id"),
            "message": msg['autoMessage'],
            "time" : timezone.now(),
            "display_name": data.get("display_name"),
            "id" : data.get("id")
            }
            messages_ref.add(message)
            messages_ref.add(auto_message)
        else:
            messages_ref.add(message)

        # Return success response
        current_time = timezone.now()

# Serialize the datetime object to a JSON-serializable format
        serialized_time = json.dumps(current_time, cls=DjangoJSONEncoder)
        pusher.trigger(data.get('sender_id'),'new-message',{'conversation_id':data.get('id'),'userId':data.get('receiver_id'),'username':data.get('sender_display_name'),'time':serialized_time})
        return JsonResponse({'success': True})
    else:
        # Return error response for unsupported HTTP method
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@api_view(['POST'])
def update_user_presence(request):
    data = request.data.copy()
    user = data.get('userId')
    doc_ref = db.collection("users").document(user)
    doc_ref.update({'online':data.get('online')})
    pusher.trigger('users','status',{'userId':user})
    return Response({'message': 'User presence updated successfully'}, status=200)

@api_view(['GET'])
def get_user_presence(request):
    userId = request.query_params.get('userId')
    print("********user presence id : ",userId)
    doc_ref = db.collection("users").document(userId).get()
    data = doc_ref.to_dict()
    
    online_status = data.get('online', None)  # Check if "online" attribute exists
    print("***** online status: ",online_status)
    return Response({'online': online_status}, status=200)


@api_view(['POST'])
def create_conversation(request):
    try:
        data = request.data.copy()
        conversations_ref = db.collection('conversations')
        sender_conversations = conversations_ref.where('participants', 'array_contains', data.get('sender_id')).stream()

        # Get conversations where both sender and receiver are participants
        common_conversations = [
            conv.reference.id for conv in sender_conversations
            if any(participant == data.get('receiver_id') for participant in conv.to_dict().get('participants', []))
        ]
        
        if not common_conversations:
            conversation_data = {
                'participants': [data.get("receiver_id"), data.get("sender_id")],
                'time': timezone.now(),
                'display_names' : [data.get("receiver_display_name"),data.get("sender_display_name"),
                ]
            }
            new_conversation_ref = db.collection("conversations").add(conversation_data)
            print("**** new conversation ref: ", new_conversation_ref)
            new_conversation_id = new_conversation_ref[1].id
            new_conversation_ref = db.collection("conversations").document(new_conversation_id)
            new_conversation_ref.update({'id':new_conversation_id})
            return JsonResponse({'message': 'Conversation created successfully'}, status=200)
        else:
            db.collection('conversations').document(common_conversations[0]).update({'time': timezone.now()})
            return JsonResponse({'message': 'Conversation already exists', 'conversation_id': common_conversations[0]}, status=200)
    except Exception as e:
        # Log or return the error message
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
def save_autoMessage(request):
    data = request.data.copy()
    if not data.get('userId'): 
        return Response({'error':'userId is required'},status=400)
    db.collection('users').document(data.get('userId')).update({'autoMessage' : data.get('message')})
    return Response({'message':'auto message updated successfully'},status=200)



@api_view(['POST'])
@csrf_exempt
def create_payment(request):
    if request.method == 'POST':
        # Extract data from request
        data = request.data.copy()
        # Example data: {'amount': '100', 'description': 'Payment for service'}
        
        # Create a new payment document
        payment_ref = db.collection('payments').document()
        payment_data ={
            'amount': data.get('amount'),
            'sender_id' : data.get('sender_id'),
            'receiver_id' : data.get('receiver_id'),
            'paid' : False,}


        payment_ref = db.collection('payments').add(payment_data)
        pusher.trigger(data.get('conversation_id'),'paiements','new-payment')

        db.collection('conversations').document(data.get('conversation_id')).update({'payment_id':payment_ref[1].id})
        return JsonResponse({'message': 'Payment created successfully','payment_id':payment_ref[1].id}, status=201)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

# API view for retrieving a payment document
@api_view(['GET'])
@csrf_exempt
def retrieve_payment(request, payment_id):
    if request.method == 'GET':
        # Retrieve payment document from Firestore
        data = request.data.copy()
        payment = db.collection('payments').document(payment_id).get().to_dict()
        
        if payment:
            return JsonResponse(payment)
        else:
            return JsonResponse({'error': 'Payment not found'}, status=404)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

# API view for deleting a payment document
@api_view(['DELETE'])
@csrf_exempt
def delete_payment(request, payment_id,conversation_id):
    if request.method == 'DELETE':
        # Delete payment document from Firestore
        data = request.data.copy()
        payment_ref = db.collection('payments').document(payment_id).delete()
        db.collection('conversations').document(conversation_id).update({'payment_id':firestore.DELETE_FIELD})
        pusher.trigger(conversation_id,'cancel payment','new-payment')

        return JsonResponse({'message': 'Payment deleted successfully'})
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

# API view for updating a payment document
@api_view(['PUT'])
@csrf_exempt
def update_payment(request, payment_id,conversation_id):
    if request.method == 'PUT':
        # Extract data from request
        data = request.POST
        # Example data: {'amount': '200', 'description': 'Updated payment'}
        
        # Update payment document in Firestore
        payment_ref = db.collection('payments').document(payment_id)
        payment_ref.update({
            'time' : timezone.now(),
            'paid' : True
        })
        pusher.trigger(conversation_id,'paiements','new-payment')
        return JsonResponse({'message': 'Payment updated successfully'})
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)


@api_view(['POST'])
@csrf_exempt
def save_feedback(request):
    if request.method == 'POST':
        try:
            data = request.data.copy()
            
            feedback_data = {
                'star': data.get('star'),
                'comment': data.get('comment'),
                'client_id': data.get('client_id'),
                'company_id': data.get('company_id'),
                'timestamp': timezone.now()}

            # Save feedback to Firestore
            if(data.get('feedback_id') == ''):
                feedback_ref = db.collection('feedback').add(feedback_data)
                feedback_id = feedback_ref[1].id
                db.collection('feedback').document(feedback_id).update({'id': feedback_id})
            else:
                feedback_id = data.get('feedback_id')
                db.collection('feedback').document(feedback_id).update(feedback_data)
            return JsonResponse({'message': 'Feedback saved successfully'}, status=201)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)

@api_view(['GET'])
@csrf_exempt
def retrieve_feedback(request):
    try:
        client_id = request.query_params.get('client_id', None)
        company_id = request.query_params.get('company_id', None)

        
        if client_id and company_id:
            # Fetch feedback for a specific user
            feedback_ref = db.collection('feedback').where('company_id', '==', company_id).where('client_id','==',client_id)
        elif company_id :
            feedback_ref = db.collection('feedback').where('company_id', '==', company_id)

        
        feedback = [fb.to_dict() for fb in feedback_ref.stream()]

        return JsonResponse(feedback, safe=False, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
