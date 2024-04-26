from .models import *
from rest_framework import serializers

# Create a model serializer
class OffresSerializer(serializers.HyperlinkedModelSerializer):
    # specify model and fields
    class Meta:
        model = Offre
        fields = ('title', 'description', 'creationDate', 'updateDate', 'user_id',
                  'depart_date', 'arrival_date', 'itinerary', 'volume', 'price',)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set partial=True to allow partial updates
        self.partial = True

class DemandesSerializer(serializers.HyperlinkedModelSerializer):
    # specify model and fields
    class Meta:
        model = Demande
        fields = ('title', 'description','creationDate','updateDate','user_id','date','depart','destination','volume','price')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set partial=True to allow partial updates
        self.partial = True


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'password','role', 'phone', 'dateInscription', 'bio','city','file','image','hideEmail')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set partial=True to allow partial updates
        self.partial = True

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
