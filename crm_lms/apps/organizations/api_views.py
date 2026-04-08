from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json

from .models import Organization, UserCurrentOrganization
from apps.core.mixins import get_current_organization


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class OrganizationsAPI(View):
    """API для получения списка организаций пользователя"""
    
    def get(self, request):
        try:
            # Суперадминистратор видит все организации
            if request.user.is_superuser:
                organizations = Organization.objects.filter(is_active=True)
            else:
                # Обычный пользователь видит только свои организации
                organizations = Organization.objects.filter(
                    members__user=request.user,
                    members__is_active=True
                ).distinct()
            
            data = []
            for org in organizations:
                data.append({
                    'id': org.id,
                    'name': org.name,
                    'description': org.description,
                    'is_active': org.is_active,
                    'logo': org.logo.url if org.logo else None,
                })
            
            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(login_required, name='dispatch')
class SwitchOrganizationAPI(View):
    """API для переключения организации"""
    
    def post(self, request, org_id):
        try:
            # Суперадминистратор может переключаться на любую организацию
            if request.user.is_superuser:
                organization = Organization.objects.get(id=org_id, is_active=True)
            else:
                # Обычный пользователь только на свои организации
                organization = Organization.objects.get(
                    id=org_id,
                    members__user=request.user,
                    members__is_active=True
                )
            
            # Обновляем текущую организацию пользователя
            user_current_org, created = UserCurrentOrganization.objects.get_or_create(
                user=request.user,
                defaults={'organization': organization}
            )
            if not created:
                user_current_org.organization = organization
                user_current_org.save()
            
            return JsonResponse({'success': True, 'organization': organization.name})
        except Organization.DoesNotExist:
            return JsonResponse({'error': 'Организация не найдена или нет доступа'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
