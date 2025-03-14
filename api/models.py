from django.db import models




class User(models.Model):
    id = models.AutoField(primary_key=True)
    bio = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    date_inscription = models.DateField(null=True, blank=True,db_column='dateInscription')
    email = models.EmailField(unique=True, max_length=255)
    file = models.CharField(max_length=255, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)
    type_user = models.IntegerField(null=True, blank=True)
    statut_user = models.IntegerField(null=True, blank=True)
    login = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    class Meta:
        db_table = 'users'
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
    class Meta:
        db_table = 'offres'
    def __str__(self):
        return self.title
	  

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

