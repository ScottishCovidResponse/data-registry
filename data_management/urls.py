from django.urls import path, include
from django.utils.text import camel_case_to_spaces
from django.views.decorators.cache import cache_page
from rest_framework import routers

from . import views, models, tables
from .rest import views as api_views

router = routers.DefaultRouter()
router.register(r'users', api_views.UserViewSet)
router.register(r'groups', api_views.GroupViewSet)

for name in models.all_models:
    url_name = camel_case_to_spaces(name).replace(' ', '_')
    router.register(url_name, getattr(api_views, name + 'ViewSet'), basename=name.lower())

urlpatterns = [
    path('', views.index, name='index'),
    path('issues/', views.IssueListView.as_view(), name='issues'),
    path('issue/<int:pk>', views.IssueDetailView.as_view(), name='issue'),
    path('api/', include(router.urls)),
    path('api/prov-report/<int:pk>/', cache_page(300)(api_views.ProvReportView.as_view()), name='prov_report'),
    path('get-token', views.get_token, name='get_token'),
    path('revoke-token', views.revoke_token, name='revoke_token'),
    path('docs/', cache_page(300)(views.doc_index), name='docs_index'),
    path('docs/<str:name>', cache_page(300)(views.docs)),
    path('tables/dataproducts', cache_page(300)(tables.data_product_table_data)),
    path('tables/externalobjects', cache_page(300)(tables.external_objects_table_data)),
    path('tables/codereporeleases', cache_page(300)(tables.code_repo_release_table_data)),
    path('api/data/<path:name>', api_views.ObjectStorageView.as_view())
]


for name in models.all_models:
    url_name = camel_case_to_spaces(name).replace(' ', '_')
    urlpatterns.append(path(url_name + '/<int:pk>', cache_page(300)(getattr(views, name + 'DetailView').as_view()),
                            name=name.lower()))
    # urlpatterns.append(path(url_name + '/<int:pk>', getattr(views, name + 'DetailView').as_view(), name=name.lower()))
    urlpatterns.append(path(url_name + 's/', getattr(views, name + 'ListView').as_view(), name=name.lower() + 's')) 
