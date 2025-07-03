from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.conf import settings

class User(models.Model):
    id = models.AutoField(primary_key=True)
    civility = models.CharField(max_length=50, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    raison_sociale = models.CharField(max_length=255, null=True, blank=True)
    siret = models.CharField(max_length=20, null=True, blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)

    bio = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    date_inscription = models.DateField(null=True, blank=True, db_column='dateInscription')
    email = models.EmailField(unique=True, max_length=255)
    file = models.FileField(upload_to='uploads/', null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    type_user = models.IntegerField(null=True, blank=True)
    statut_user = models.IntegerField(null=True, blank=True)
    password = models.CharField(max_length=255)
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    enabled = models.BooleanField(null=True, blank=True)
    emailVerified = models.BooleanField(null=True, blank=True)
    last_login    = models.DateTimeField(null=True, blank=True)
    date_joined   = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        db_table = 'users'

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = now()
        self.save()

    def __str__(self):
        return str(self.id)
class Offre(models.Model):
    id_offre = models.AutoField(primary_key=True,db_column='id_offre')
    destination_date_start = models.DateField(null=True, blank=True,db_column='destinationDateStart')
    creation_date = models.DateTimeField(auto_now_add=True,db_column="creationDate")
    depart_date_start = models.DateField(null=True, blank=True,db_column='departDateStart') 
    destination = models.CharField(max_length=255, null=True, blank=True)
    origin = models.CharField(max_length=255, null=True, blank=True)
    route = models.TextField(null=True, blank=True)
    update_date = models.DateTimeField(null=True, blank=True,db_column='updateDate')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offres')
    depart_date_end = models.DateField(null=True, blank=True,db_column='departDateEnd')
    destination_date_end = models.DateField(null=True, blank=True,db_column='destinationDateEnd')
    prix = models.IntegerField()
    volume = models.IntegerField()
    reference = models.TextField(null=True, blank=True)
    ascenseur_depart=models.BooleanField(null=True, blank=True,db_column='ascenseur_depart')
    ascenseur_arrivee=models.BooleanField(null=True, blank=True,db_column='ascenseur_arrivee')
    monte_meuble_depart=models.BooleanField(null=True, blank=True,db_column='monte_meuble_depart')
    monte_meuble_arrivee=models.BooleanField(null=True, blank=True,db_column='monte_meuble_arrivee')
    escalier_depart=models.BooleanField(null=True, blank=True,db_column='escalier_depart')
    escalier_arrivee=models.BooleanField(null=True, blank=True,db_column='escalier_arrivee')
    direct_depart=models.BooleanField(null=True, blank=True,db_column='direct_depart')
    direct_arrivee=models.BooleanField(null=True, blank=True,db_column='direct_arrivee')
    depart_etage=models.TextField(null=True, blank=True,db_column='depart_etage')
    arrivee_etage=models.TextField(null=True, blank=True,db_column='arrivee_etage')
    depart_pres=models.TextField(null=True, blank=True,db_column='depart_pres')
    arrivee_pres=models.TextField(null=True, blank=True,db_column='arrivee_pres')
    commentaire=models.TextField(null=True, blank=True,db_column='commentaire')
    type_offre = models.ForeignKey(
        'Parameter', 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='offres',
        db_column='type_offre'
    )
    class Meta:
        db_table = 'offres'
    def __str__(self):
        return f"Offre #{self.id_offre}"
	  
class Parameter(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)

    class Meta:
        db_table = 'parameters'
        managed = False

    def __str__(self):
        return self.name

class Demande(models.Model):
	id = models.IntegerField(primary_key=True)
	title = models.CharField(max_length=200)
	description = models.TextField()
	creationDate = models.DateTimeField(auto_now_add=True)
	updateDate = models.DateTimeField(auto_now=True) 
	date = models.TextField(null=True, blank=True)
	depart = models.TextField()
	destination = models.TextField()
	volume = models.FloatField()
	price = models.FloatField()
	user_id = models.TextField()

	def __str__(self):
		return self.title


class Notification(models.Model):
    user_id = models.TextField()
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f'Notification for {self.user.username}'

    class Meta:
        ordering = ['-timestamp']



class RetourVide(models.Model):
    TYPE_CAMION_CHOICES = [
        ('VL', 'VL'),
        ('PL', 'PL'),
    ]
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='retour_vide')
    volume = models.DecimalField(max_digits=10, decimal_places=2)
    type_camion = models.CharField(max_length=2, choices=TYPE_CAMION_CHOICES)
    avec_hayon = models.BooleanField()
    depart_date_start  = models.DateField()
    depart_date_end    = models.DateField(null=True, blank=True)
    arrival_date_start = models.DateField()
    arrival_date_end   = models.DateField(null=True, blank=True)
    detour_possible    = models.BooleanField()
    origin = models.CharField(max_length=2, blank=True, null=True)
    destination   = models.CharField(max_length=2, blank=True, null=True)
    itineraire = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'retour vide #{self.id} by {self.user}'
    class Meta:
        db_table = 'retour_vide'
        managed = False



class Proposition(models.Model):
    """
    Modèle pour les propositions faites à un retour vide.
    """
    STATUS_CHOICES = [
        ('EN_COURS', 'En cours'),
        ('REFUSEE',  'Refusée'),
        ('CLOTUREE', 'Clôturée'),
    ]
    PASSAGE_CHOICES = [
        ('ASC', 'Ascenseur'),
        ('ESC', 'Escalier'),
    ]

    # Référence au retour vide
    retour = models.ForeignKey(RetourVide, on_delete=models.CASCADE, )

    # Si c’est un PRO connecté, on stocke user_pro. Sinon user_pro = None et on remplit les champs “Particulier” suivants.
    user_pro = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    # Champs “Particulier” (obligatoires si user_pro=None)
    civility   = models.CharField(max_length=20, null=True, blank=True)  # ex. “Mr”, “Mme”
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name  = models.CharField(max_length=255, null=True, blank=True)
    email      = models.EmailField(max_length=255, null=True, blank=True)
    phone      = models.CharField(max_length=50, null=True, blank=True)

    # Données de la proposition
    volume_propose = models.DecimalField(max_digits=10, decimal_places=2)
    biens           = models.TextField(help_text="Liste des biens à transporter (texte libre)")

    periode_souhaitee_start = models.DateField()
    periode_souhaitee_end   = models.DateField()
    flexibilite    = models.BooleanField(default=False)

    # Détails de chargement
    adresse_chargement = models.CharField(max_length=255)
    etage_chargement   = models.IntegerField()
    passage_chargement = models.CharField(max_length=10, choices=PASSAGE_CHOICES)

    # Détails de livraison
    adresse_livraison  = models.CharField(max_length=255)
    etage_livraison    = models.IntegerField()
    passage_livraison  = models.CharField(max_length=10, choices=PASSAGE_CHOICES)

    statut            = models.CharField(max_length=10, choices=STATUS_CHOICES, default='EN_COURS')
    code_confidentiel = models.CharField(max_length=10, null=True, blank=True)

    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Proposition #{self.id} pour Retour #{self.retour_id}"
    
    class Meta:
        db_table = 'proposition'
        managed = False
        ordering = ['-created_at']