from .models import *
from rest_framework import serializers

# Create a model serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'bio', 'city', 'date_inscription', 'email', 'file', 'name', 'phone', 'role', 'type_user', 'statut_user', 'login', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class OffreSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)
    
    class Meta:
        model = Offre
        fields = ['id_offre', 'destination_date_start', 'creation_date', 'depart_date_start', 'destination', 'origin', 'route', 'update_date', 'user', 'user_id', 'depart_date_end', 'destination_date_end', 'prix', 'volume']
 
class DemandesSerializer(serializers.HyperlinkedModelSerializer):
    # specify model and fields
    class Meta:
        model = Demande
        fields = ('title', 'description','creationDate','updateDate','user_id','date','depart','destination','price')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set partial=True to allow partial updates
        self.partial = True


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
