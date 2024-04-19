# basic URL Configurations
from django.urls import include, path
# import routers
from rest_framework import routers

# import everything from views
from .views import *

# define the router
router = routers.DefaultRouter()

# define the router path and viewset to be used
router.register(r'offres', OffresViewSet, basename='offres')
router.register(r'demandes', DemandesViewSet, basename='demandes')
router.register(r'register',RegisterViewSet,basename='register')
router.register(r'ad-api/companies', AdminCompaniesViewSet, basename='admin_companies'),
router.register(r'ad-api/clients', AdminClientsViewSet, basename='admin_clients')




# specify URL Path for rest_framework
urlpatterns = [
	path('login/', LoginAPIView.as_view(), name='login'),
	path('profile/', ProfileView.as_view(), name='user_profile'),
	path('', include(router.urls)),
	path('api-auth/', include('rest_framework.urls')),
	path('ad-api/companies/<str:pk>/download-file/', download_file, name='download_file'),
]
