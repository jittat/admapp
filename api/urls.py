from django.urls import path, include
from rest_framework import routers, serializers, viewsets

from appl.models import Campus, Faculty


# Serializers define the API representation.
class CampusSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Campus
        fields = ['id', 'title', 'short_title']

# ViewSets define the view behavior.
class CampusViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Campus.objects.all()
    serializer_class = CampusSerializer

# Serializers define the API representation.
class FacultySerializer(serializers.HyperlinkedModelSerializer):
    campus = CampusSerializer(read_only=True)
    class Meta:
        model = Faculty
        fields = ['id', 'title', 'campus', 'ku_code']

# ViewSets define the view behavior.
class FacultyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Faculty.objects.all()
    serializer_class = FacultySerializer

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'campuses', CampusViewSet)
router.register(r'faculties', FacultyViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
