from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse

from .admin import TIPOS_POR_ENTIDADE
from .models import Documento

T = Documento.Tipo


@staff_member_required
def ajax_objetos(request):
    """Retorna objetos e tipos permitidos para o ContentType recebido."""
    try:
        ct = ContentType.objects.get(pk=request.GET.get('ct'))
    except (ContentType.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'objetos': [], 'tipos': []})

    model = ct.model_class()
    objetos = [{'id': obj.pk, 'texto': str(obj)} for obj in model.objects.all()]
    tipos_permitidos = TIPOS_POR_ENTIDADE.get(ct.model, [])
    tipos = [{'valor': v, 'label': l} for v, l in T.choices if v in tipos_permitidos]

    return JsonResponse({'objetos': objetos, 'tipos': tipos})
