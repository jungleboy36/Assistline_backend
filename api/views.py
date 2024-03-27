from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from .serializers import OffresSerializer
from firebase_admin import firestore
from django.utils import timezone

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
