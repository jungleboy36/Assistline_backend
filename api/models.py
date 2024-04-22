from django.db import models


class Offre(models.Model):
	title = models.CharField(max_length=200)
	description = models.TextField()
	creationDate = models.DateTimeField(auto_now_add=True)
	updateDate = models.DateTimeField(auto_now=True) 
	user_id = models.TextField()
	depart_date = models.DateTimeField(null=True, blank=True)
	arrival_date = models.DateTimeField(null=True, blank=True)
	itinerary =	models.TextField()
	volume = models.FloatField()
	price = models.FloatField()
	def __str__(self):
		return self.title

class Demande(models.Model):
	id = models.IntegerField(primary_key=True)
	title = models.CharField(max_length=200)
	description = models.TextField()
	creationDate = models.DateTimeField(auto_now_add=True)
	updateDate = models.DateTimeField(auto_now=True) 
	user_id = models.TextField()

	def __str__(self):
		return self.title

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)
    role = models.CharField(max_length=20)
    phone = models.IntegerField(null=True, blank=True)
    dateInscription = models.DateTimeField(auto_now_add=True)
    bio = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    image = models.TextField(blank=True)
    file = models.TextField(blank=True, null=True)
    offres = models.TextField(blank=True)
    demandes = models.TextField(blank=True)
	  # Only for companies
