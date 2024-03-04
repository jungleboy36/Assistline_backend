from .models import Offre
from rest_framework import serializers

# Create a model serializer
class OffresSerializer(serializers.HyperlinkedModelSerializer):
    # specify model and fields
    class Meta:
        model = Offre
        fields = ('id','title', 'description')
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set partial=True to allow partial updates
        self.partial = True