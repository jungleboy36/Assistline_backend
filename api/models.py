from django.db import models


class Offre(models.Model):
	id = models.IntegerField(primary_key=True)
	title = models.CharField(max_length=200)
	description = models.TextField()

	def __str__(self):
		return self.title
