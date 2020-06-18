from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.db import models
from django.core import validators
from dynamic_validator import ModelFieldRequiredMixin
import uuid


class BaseModel(ModelFieldRequiredMixin, models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    updated_by = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_updated',
            editable=False,
            verbose_name='last updated by',
            )
    last_updated = models.DateField(auto_now=True)

    EXTRA_DISPLAY_FIELDS = ()
    REQUIRED_FIELDS = ['name']

    def reverse_name(self):
        return self.__class__.__name__.lower()

    class Meta:
        abstract = True
        ordering = ['name', '-last_updated']

    def __str__(self):
        return self.name


class DataObject(BaseModel):
    # object_uid = models.UUIDField(default=uuid.uuid4, editable=False)
    responsible_person = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name='%(app_label)s_%(class)s_responsible_for',
            )
    issues = GenericRelation('Issue')

    class Meta:
        abstract = True


class DataObjectVersion(DataObject):
    VERSIONED_OBJECT = ''
    version_identifier = models.CharField(max_length=255)
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='superseded_by')

    REQUIRED_FIELDS = []
    
    @property
    def name(self):
        return '%s (version %s)' % (getattr(self, self.VERSIONED_OBJECT).name, self.version_identifier)

    class Meta:
        abstract = True


class Issue(BaseModel):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    data_object = GenericForeignKey('content_type', 'object_id')
    severity = models.PositiveSmallIntegerField(default=1)
    desc = models.TextField(max_length=1024, null=False, blank=False, verbose_name='description')

    def __str__(self):
        return '%s [Severity %s]' % (self.name, self.severity)


class DataProductType(BaseModel):
    description = models.TextField(max_length=1024, null=False, blank=False)


class StorageType(BaseModel):
    description = models.TextField(max_length=1024, null=True, blank=True)


class URIField(models.URLField):
    default_validators = []


class StorageRoot(BaseModel):
    type = models.ForeignKey(StorageType, on_delete=models.CASCADE, null=False)
    description = models.TextField(max_length=1024, null=True, blank=True)
    uri = models.CharField(max_length=1024, null=False, blank=False)
    # uri = URIField(max_length=1024, null=False, blank=False)


class DataStore(DataObject):
    store_root = models.ForeignKey(StorageRoot, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=True, blank=True)
    path = models.CharField(max_length=1024, null=True, blank=True)
    # toml_text = models.TextField(max_length=1024, null=True, blank=True)
    hash = models.CharField(max_length=1024, null=True, blank=True)
    local_cache_url = models.URLField(max_length=1024, null=True, blank=True)


class Accessibility(BaseModel):
    description = models.TextField(max_length=1024, null=True, blank=True)
    access_info = models.CharField(max_length=1024, null=False, blank=False)


class SourceType(BaseModel):
    description = models.CharField(max_length=255, null=False, blank=False)


class Source(DataObject):
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    source_type = models.ForeignKey(SourceType, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)


class SourceVersion(DataObjectVersion):
    VERSIONED_OBJECT = 'source'
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)


class DataProduct(DataObject):
    EXTRA_DISPLAY_FIELDS = ('versions',)
    description = models.TextField(max_length=1024, null=False, blank=False)


class DataProductDataType(BaseModel):
    description = models.CharField(max_length=255)
    type = models.ForeignKey(DataProductType, on_delete=models.CASCADE)


class ProcessingScript(DataObject):
    EXTRA_DISPLAY_FIELDS = ('versions',)
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)


class ProcessingScriptVersion(DataObjectVersion):
    VERSIONED_OBJECT = 'processing_script'
    processing_script = models.ForeignKey(ProcessingScript, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)


class DataProductVersion(DataObjectVersion):
    VERSIONED_OBJECT = 'data_product'
    EXTRA_DISPLAY_FIELDS = ('components', 'model_runs')
    data_product = models.ForeignKey(DataProduct, on_delete=models.CASCADE, related_name='versions')
    data_type = models.ForeignKey(DataProductDataType, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)
    processing_script_version = models.ForeignKey(ProcessingScriptVersion, on_delete=models.CASCADE)
    source_versions = models.ManyToManyField(SourceVersion, blank=True)


class DataProductVersionComponent(DataObject):
    EXTRA_DISPLAY_FIELDS = ('model_runs',)
    data_product_version = models.ForeignKey(DataProductVersion, on_delete=models.CASCADE, related_name='components')


class Model(DataObject):
    EXTRA_DISPLAY_FIELDS = ('versions',)
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)


class ModelVersion(DataObjectVersion):
    EXTRA_DISPLAY_FIELDS = ('model_runs',)
    VERSIONED_OBJECT = 'model'
    model = models.ForeignKey(Model, on_delete=models.CASCADE, related_name='versions')
    store = models.ForeignKey(DataStore, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024, null=False, blank=False)
    accessibility = models.ForeignKey(Accessibility, on_delete=models.CASCADE)


class ModelRun(DataObject):
    model_version = models.ForeignKey(ModelVersion, on_delete=models.CASCADE, related_name='model_runs')
    release_date = models.DateField()
    description = models.TextField(max_length=1024, null=True, blank=True)
    model_config = models.TextField(max_length=1024, null=True, blank=True)
    submission_script = models.TextField(max_length=1024, null=True, blank=True)
    inputs = models.ManyToManyField(DataProductVersionComponent, blank=True, related_name='model_runs')
    outputs = models.ManyToManyField(DataProductVersion, blank=True, related_name='model_runs')
    supersedes = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)

    @property
    def name(self):
        return '%s (Run %s)' % (self.model_version.name, self.release_date)


all_object_models = dict(
    (name, cls) for (name, cls) in globals().items() 
    if isinstance(cls, type) and issubclass(cls, DataObject) and name not in ('DataObject', 'DataObjectVersion')
)

all_models = dict(
    (name, cls) for (name, cls) in globals().items()
    if isinstance(cls, type) and issubclass(cls, BaseModel) and name not in ('BaseModel', 'DataObject', 'DataObjectVersion')
)

