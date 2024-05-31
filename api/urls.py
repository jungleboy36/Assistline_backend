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
	path('get-role/<str:id_token>/', GetRoleFromToken.as_view(), name='get-role'),
	path('status/<str:pk>/',check_status, name='check_status'),
	path('stats', DocumentCountAPIView.as_view(), name='document_count_api'),
	path('notifications/', NotificationsAPIView.as_view(), name='notifications_api'),
	path('notifications/mark-all-as-read/',mark_all_as_read , name='mark_all_as_read'),
	path('conversations/<str:user_id>/', get_conversations, name='get_conversations'),
    path('messages/<str:conversation_id>/', get_messages, name='get_messages'),
    path('send/', create_message, name='create_message'),
	path('update-user-presence/', update_user_presence, name='update_user_presence'),
	path('get-user-presence/', get_user_presence, name='get_user_presence'),
    path('create-conversation/', create_conversation, name='create_conversation'),
	path('send-email/',send_email,name='send_email'),
	path('auto-message/',save_autoMessage,name='save_autoMessage'),
	path('create_payment/',create_payment,name='create_payment'),
	path('update_payment/<str:payment_id>/<str:conversation_id>/',update_payment,name='update_payment'),
	path('retrieve_payment/<str:payment_id>/',retrieve_payment,name='retrieve_payment'),
	path('delete_payment/<str:payment_id>/<str:conversation_id>/',delete_payment,name='delete_payment'),
	path('save_feedback/',save_feedback,name='save_feedback'),
	path('retrieve_feedback/',retrieve_feedback,name='retrieve_feedback'),



]

