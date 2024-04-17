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


class OffresViewSet(viewsets.ViewSet):
    serializer_class = OffresSerializer
    def list(self, request):
        offres = firestore.client().collection('offres').get()
        data = [{'id': doc.id, **doc.to_dict()} for doc in offres]  # Add 'id' field with document ID
        #print("****list data :",data)
        return Response(data)

    def create(self, request): 
        serializer = OffresSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            i = firestore.client().collection('id').document('number').get().to_dict().get('id')
            #print("***** i : ", i)
            id_value =i
            firestore.client().collection('id').document('number').set({'id':i+1})
            data['creationDate'] = timezone.now()
            firestore.client().collection('offres').document(str(id_value)).set(data)
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
    def retrieve(self, request, pk=None):
        offre = firestore.client().collection('offres').document(pk).get()
        if offre.exists:
            data = offre.to_dict()
            return Response(data,status=status.HTTP_200_OK)
        return Response({'error': 'Offre not found'}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, pk=None):
        serializer = OffresSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            data['updateDate'] = timezone.now()
            firestore.client().collection('offres').document(pk).set(data,merge= True)
            return Response(data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return self.update(request, pk)

    def destroy(self, request, pk=None):
        firestore.client().collection('offres').document(pk).delete()
        return Response(status=status.HTTP_200_OK)

class DemandesViewSet(viewsets.ViewSet):
    serializer_class = DemandesSerializer
    def list(self, request):
        demandes = firestore.client().collection('demandes').get()
        data = [{'id': doc.id, **doc.to_dict()} for doc in demandes]  # Add 'id' field with document ID
        #print("****list data :",data)
        return Response(data)

    def create(self, request): 
        serializer = DemandesSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            i = firestore.client().collection('id').document('number').get().to_dict().get('id')
            #print("***** i : ", i)
            id_value =i
            firestore.client().collection('id').document('number').set({'id':i+1})
            data['creationDate'] = timezone.now()
            firestore.client().collection('demandes').document(str(id_value)).set(data)
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
        # Retrieve the role from the request data
        role = request.data.get('role')

        # Initialize the serializer with the request data
        serializer = UserSerializer(data=request.data)

        # Check if the data is valid
        if serializer.is_valid():
            # Save the user data in the Django database
            instance = serializer.save()

            # Retrieve the data from the serializer
            data = serializer.data
            user_data = {
                'email': data['email'],
                'password': data['password'],  # Make sure the password is securely stored
            }

            try:
                # Create the user in Firebase Authentication
                firebase_user = auth.create_user(**user_data)
                auth.update_user(firebase_user.uid, display_name=data['name'])  # Set the display name

                # Create a Firestore client
                db = firestore.client()
                
                # Use the Firebase Authentication user ID (uid) as the document ID
                uid = firebase_user.uid
                
                # Save the user data in Firestore under the 'users' collection with the user's UID as the document ID
                user_data = {
                    'name': data['name'],
                    'email': data['email'],
                    'role': data['role'],
                    'phone': data.get('phone'),
                    'dateInscription': data['dateInscription'],
                    'bio': data.get('bio'),
                    'city': data.get('city'),
                    
                }
                db.collection('users').document(uid).set(user_data)

                # Return a successful response with the serialized data and a status code of 201_CREATED
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                # Handle any errors that occur during user creation in Firebase
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # If the data is invalid, return the serializer errors and a status code of 400_BAD_REQUEST
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            try:
                user = auth.get_user_by_email(email)
                # Verify user's password
                auth_user = auth.update_user(
                    user.uid,
                    password=password
                )
                # Return success response or user data
                return Response({'message': 'Login successful', 'user': {
                    'uid': auth_user.uid,
                    'email': auth_user.email,
                    'display_name': auth_user.display_name,
                    # Add other user attributes as needed
                }}, status=status.HTTP_200_OK)
            except auth.AuthError as e:
                return Response({'error': 'Login failed', 'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
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