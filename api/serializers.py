from .models import *
from rest_framework import serializers

# Create a model serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'      
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


class RetourVideSerializer(serializers.ModelSerializer):
    class Meta:
        model = RetourVide
        fields = '__all__'
        read_only_fields = (
            'id',
            'user',
            'created_at',
            'updated_at',
        )


class PropositionSerializer(serializers.ModelSerializer):
    # Si user_pro est présent (PRO connecté), on ignore les champs Particulier.
    # Sinon, on exige ces champs.
    civility   = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name  = serializers.CharField(required=False, allow_blank=True)
    email      = serializers.EmailField(required=False, allow_blank=True)
    phone      = serializers.CharField(required=False, allow_blank=True)

    # user_pro est write-only : si PRO connecté, on ne l’envoie pas dans le JSON,
    # mais on l’ajoute en back-end dans perform_create
    user_pro = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, required=False
    )

    class Meta:
        model = Proposition
        fields = [
            'id',
            'retour',
            'user_pro',
            'civility', 'first_name', 'last_name', 'email', 'phone',
            'volume_propose', 'biens',
            'periode_souhaitee_start', 'periode_souhaitee_end',
            'flexibilite',
            'adresse_chargement', 'etage_chargement', 'passage_chargement',
            'adresse_livraison', 'etage_livraison', 'passage_livraison',
            'statut', 'code_confidentiel',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'statut', 'code_confidentiel', 'created_at', 'updated_at']

    def validate(self, data):
        """
        Si user_pro est None (Particulier), on exige civility/first_name/last_name/email/phone non vides.
        """
        user_pro = data.get('user_pro', None)
        if not user_pro:
            missing = []
            for field in ['civility', 'first_name', 'last_name', 'email', 'phone']:
                if not data.get(field):
                    missing.append(field)
            if missing:
                raise serializers.ValidationError({
                    field: 'Ce champ est requis pour un particulier.' for field in missing
                })
        return data

    def create(self, validated_data):
        # Si PRO connecté, user_pro sera sur request.user dans perform_create
        return super().create(validated_data)

