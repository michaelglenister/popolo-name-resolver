from django.conf.urls import patterns, include

urlpatterns = []

urlpatterns += patterns('',
    (r'^', include('popolo_name_resolver.urls')),
)
