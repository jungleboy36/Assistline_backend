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

from functools import wraps

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
    @requires_role(['client', 'company'])
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
    @requires_role(['company'])
    def retrieve(self, request, pk=None):
        offre = firestore.client().collection('offres').document(pk).get()
        if offre.exists:
            data = offre.to_dict()
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
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @requires_role(['client', 'company'])
    def retrieve(self, request, pk=None):
        offre = firestore.client().collection('demandes').document(pk).get()
        if offre.exists:
            data = offre.to_dict()
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
        allowed_fields = ['name', 'phone', 'bio', 'city', 'image', 'role','hideEmail']
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

@requires_role(['admin'])
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
        body = f'Click the following link to verify your email: {verification_link} After Confirmation you will have to wait until the admin activates your account after verifying the uploaded files0'

    message.attach(MIMEText(body, 'plain'))

    # Create SMTP session
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # Enable TLS
        server.login(gmail_sender_email, gmail_app_password)
        server.sendmail(gmail_sender_email, receiver_email, message.as_string())

#send_verification_email('achrafhafsia9@gmail.com','test')


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

