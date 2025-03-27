from .models import *
from rest_framework import serializers

# Create a model serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'bio', 'city', 'date_inscription', 'email', 'file', 'name', 'phone', 'role', 'type_user', 'statut_user', 'password', 'otp', 'otp_created_at', 'enabled', 'emailVerified']
        extra_kwargs = {'password': {'write_only': True}}
        file = serializers.SerializerMethodField()

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
        
    def get_file(self, obj):
        request = self.context.get('request')
        if obj.file:
            return request.build_absolute_uri(obj.file.url)
        return None


class OffreSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Only returns the user ID
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)  
    class Meta:
        model = Offre
        fields = ['id_offre', 'destination_date_start', 'creation_date', 'depart_date_start', 'destination', 'origin', 'route', 'update_date', 'user','user_id', 'depart_date_end', 'destination_date_end', 'prix', 'volume']
 
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
