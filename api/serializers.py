from .models import *
from rest_framework import serializers

# Create a model serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
                    'id', 'civility', 'first_name', 'last_name',
                    'raison_sociale', 'siret', 'contact_name',
                    'bio', 'city', 'date_inscription', 'email', 'file', 'phone',
                    'role', 'type_user', 'statut_user', 'password',
                    'otp', 'otp_created_at', 'enabled', 'emailVerified'
                ]        
        extra_kwargs = {'password': {'write_only': True}}
        file = serializers.SerializerMethodField()

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def get_file(self, obj):
        request = self.context.get('request')
        if obj.file:
            url = request.build_absolute_uri(file.url).replace('http://', 'https://')
        return None


class OffreSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)  # Only returns the user ID
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='user', write_only=True)  
    class Meta:
        model = Offre
        fields = [
            'id_offre',
            'destination_date_start',
            'creation_date',
            'depart_date_start',
            'depart_date_end',
            'destination_date_end',
            'destination',
            'origin',
            'route',
            'update_date',
            'prix',
            'volume',
            'reference',
            'type_offre',

            # New Passage / Equipment Booleans
            'ascenseur_depart',
            'ascenseur_arrivee',
            'monte_meuble_depart',
            'monte_meuble_arrivee',
            'escalier_depart',
            'escalier_arrivee',
            'direct_depart',
            'direct_arrivee',

            # Etage & Prescriptions
            'depart_etage',
            'arrivee_etage',
            'depart_pres',
            'arrivee_pres',

            # Commentaire
            'commentaire',

            # User relation
            'user',
            'user_id',
        ] 
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


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ['id', 'name']  # Add other fields as needed