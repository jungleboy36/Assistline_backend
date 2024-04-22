from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .serializers import *
from firebase_admin import firestore
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

class OffresViewSet(viewsets.ViewSet):
    serializer_class = OffresSerializer

    def list(self, request):
        # Check if user_id is provided in the query parameters
        user_id = request.query_params.get('user_id')
        
        if user_id:
            # If user_id is provided, filter offers by user_id
            offres = firestore.client().collection('offres').where('user_id', '==', user_id).get()
        else:
            # If user_id is not provided, list all offers
            offres = firestore.client().collection('offres').get()
        
        data = [{'id': doc.id, **doc.to_dict()} for doc in offres]
        return Response(data)

    def create(self, request):
        serializer = OffresSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['creationDate'] = timezone.now()
            firestore.client().collection('offres').add(data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = OffresSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['updateDate'] = timezone.now()
            firestore.client().collection('offres').document(pk).set(data, merge=True)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        firestore.client().collection('offres').document(pk).delete()
        return Response(status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        offre = firestore.client().collection('offres').document(pk).get()
        if offre.exists:
            data = offre.to_dict()
            return Response(data,status=status.HTTP_200_OK)
        return Response({'error': 'Demand not found'}, status=status.HTTP_404_NOT_FOUND)



class DemandesViewSet(viewsets.ViewSet):
    serializer_class = DemandesSerializer

    def list(self, request):
        user_id = request.user.id  # Assuming user ID is available in the request
        demandes = firestore.client().collection('demandes').where('user_id', '==', user_id).get()
        data = [{'id': doc.id, **doc.to_dict()} for doc in demandes]
        return Response(data)

    def create(self, request):
        serializer = DemandesSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data

            data['creationDate'] = timezone.now()
            data['user_id'] = request.user.id  # Associate demand with user
            firestore.client().collection('demandes').add(data)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def retrieve(self, request, pk=None):
        offre = firestore.client().collection('demandes').document(pk).get()
        if offre.exists:
            data = offre.to_dict()
            return Response(data,status=status.HTTP_200_OK)
        return Response({'error': 'Demand not found'}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        serializer = DemandesSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['updateDate'] = timezone.now()
            firestore.client().collection('demandes').document(pk).set(data,merge= True)
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

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

                # Return success response with the token
                return Response({
                    'message': 'Login successful',
                    'token': token
                }, status=status.HTTP_200_OK)
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
        allowed_fields = ['name', 'phone', 'bio', 'city', 'image', 'role']
        filtered_data = {field: updated_data[field] for field in allowed_fields if field in updated_data}

        # Update Firestore document
        user_doc_ref.update(filtered_data)
        
        # Return success response
        return JsonResponse({'message': 'Profile updated successfully'}, status=status.HTTP_200_OK)




class AdminCompaniesViewSet(viewsets.ViewSet):
    def list(self, request):
        # List all companies (users with 'company' role)
        db = firestore.client()
        users_ref = db.collection('users').where('role', '==', 'company')
        companies = users_ref.stream()

        company_list = []
        for company in companies:
            company_data = company.to_dict()
            company_data['uid'] = company.id
            company_list.append(company_data)

        return Response(company_list, status=status.HTTP_200_OK)

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


class AdminClientsViewSet(viewsets.ViewSet):
    def list(self, request):
        # List all companies (users with 'company' role)
        db = firestore.client()
        users_ref = db.collection('users').where('role', '==', 'client')
        clients = users_ref.stream()

        client_list = []
        for client in clients:
            client_data = client.to_dict()
            client_data['uid'] = client.id
            client_list.append(client_data)

        return Response(client_list, status=status.HTTP_200_OK)

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

    def retrieve(self, request, pk=None):
        # Retrieve user details and file URL
        db = firestore.client()
        user_doc = db.collection('users').document(pk).get()

        if not user_doc.exists:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user_data = user_doc.to_dict()

        # Return the user data
        return Response(user_data, status=status.HTTP_200_OK)