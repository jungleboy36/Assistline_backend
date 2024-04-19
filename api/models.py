from django.db import models


class Offre(models.Model):
	id = models.IntegerField(primary_key=True)
	title = models.CharField(max_length=200)
	description = models.TextField()
	creationDate = models.DateTimeField(auto_now_add=True)
	updateDate = models.DateTimeField(auto_now=True) 
	def __str__(self):
		return self.title

class Demande(models.Model):
	id = models.IntegerField(primary_key=True)
	title = models.CharField(max_length=200)
	description = models.TextField()
	creationDate = models.DateTimeField(auto_now_add=True)
	updateDate = models.DateTimeField(auto_now=True) 
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
    file = models.TextField(blank=True, null=True)  # Only for companies
