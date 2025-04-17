from django.db import models
from django.contrib.auth.hashers import make_password, check_password


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

