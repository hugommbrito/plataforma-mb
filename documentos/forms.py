from django import forms
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType

from config.dynamic_form import DynamicSchemaFormMixin
from unfold.widgets import UnfoldAdminSelectWidget
from .models import Documento


class _DynamicChoiceField(forms.ChoiceField):
    """ChoiceField que não valida se o valor está nas choices (choices são populadas via JS)."""
    def validate(self, value):
        forms.Field.validate(self, value)


def _choices_entidades():
    """Detecta dinamicamente modelos com GenericRelation(Documento) via introspecção."""
    modelos = []
    from django.apps import apps
    for model in apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, GenericRelation) and field.related_model is Documento:
                modelos.append(model)
                break
    modelos.sort(key=lambda m: m._meta.verbose_name)
    choices = [('', '---------')]
    for model in modelos:
        ct = ContentType.objects.get_for_model(model)
        choices.append((ct.pk, model._meta.verbose_name.capitalize()))
    return choices


class DocumentoForm(DynamicSchemaFormMixin, forms.ModelForm):
    schema = Documento.METADADOS_SCHEMA

    entidade = forms.ChoiceField(
        label='Entidade',
        widget=UnfoldAdminSelectWidget(),
    )
    objeto = _DynamicChoiceField(
        label='Objeto',
        widget=UnfoldAdminSelectWidget(),
        choices=[('', '---------')],
    )

    class Meta:
        model = Documento
        exclude = ['metadados', 'content_type', 'object_id']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['entidade'].choices = _choices_entidades()

        instance = self.instance
        if instance and instance.pk and instance.content_type_id:
            model = instance.content_type.model_class()
            self.fields['objeto'].choices = [('', '---------')] + [
                (obj.pk, str(obj)) for obj in model.objects.all()
            ]
            self.initial['entidade'] = instance.content_type_id
            self.initial['objeto'] = instance.object_id

    def clean(self):
        cleaned = super().clean()
        ct_id = cleaned.get('entidade')
        obj_id = cleaned.get('objeto')

        if not ct_id:
            self.add_error('entidade', 'Selecione uma entidade.')
            return cleaned
        if not obj_id:
            self.add_error('objeto', 'Selecione um objeto.')
            return cleaned

        try:
            ct = ContentType.objects.get(pk=ct_id)
            model = ct.model_class()
            model.objects.get(pk=obj_id)
        except Exception:
            raise forms.ValidationError('Vínculo inválido.')

        cleaned['_content_type'] = ct
        cleaned['_object_id'] = int(obj_id)
        return cleaned

    def save(self, commit=True):
        # DynamicSchemaFormMixin.save(commit=False) define metadados e retorna a instância
        instance = super().save(commit=False)
        instance.content_type = self.cleaned_data['_content_type']
        instance.object_id = self.cleaned_data['_object_id']
        if commit:
            instance.save()
            self.save_m2m()
        return instance
