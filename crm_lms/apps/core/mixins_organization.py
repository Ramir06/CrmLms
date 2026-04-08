from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

class OrganizationFilterMixin:
    """
    Миксин для фильтрации queryset по текущей организации пользователя
    """
    
    def get_organization_queryset(self, queryset):
        """
        Фильтрует queryset по организации текущего пользователя
        """
        user = self.request.user
        
        # Суперадмин видит все
        if user.is_superuser:
            return queryset
        
        # Получаем организацию пользователя
        current_org = getattr(user, 'current_organization', None)
        if not current_org:
            # Если у пользователя нет текущей организации, пробуем получить первую
            user_orgs = user.organizations.all()
            if user_orgs.exists():
                current_org = user_orgs.first()
            else:
                # Если нет организаций, возвращаем пустой queryset
                return queryset.none()
        
        # Фильтрация по организации
        if hasattr(queryset.model, 'organization'):
            return queryset.filter(organization=current_org)
        elif hasattr(queryset.model, 'student') and hasattr(queryset.model.student, 'organization'):
            return queryset.filter(student__organization=current_org)
        elif hasattr(queryset.model, 'mentor') and hasattr(queryset.model.mentor, 'organization'):
            return queryset.filter(mentor__organization=current_org)
        elif hasattr(queryset.model, 'course') and hasattr(queryset.model.course, 'organization'):
            return queryset.filter(course__organization=current_org)
        elif hasattr(queryset.model, 'lead') and hasattr(queryset.model.lead, 'organization'):
            return queryset.filter(lead__organization=current_org)
        elif hasattr(queryset.model, 'payment') and hasattr(queryset.model.payment, 'student'):
            return queryset.filter(payment__student__organization=current_org)
        else:
            # Если не найдено поле для фильтрации, возвращаем queryset без изменений
            return queryset
    
    def get_queryset(self):
        """
        Переопределяем get_queryset для применения фильтрации
        """
        queryset = super().get_queryset()
        return self.get_organization_queryset(queryset)


class OrganizationContextMixin:
    """
    Миксин для добавления текущей организации в контекст
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        current_org = getattr(user, 'current_organization', None)
        
        if not current_org and not user.is_superuser:
            user_orgs = user.organizations.all()
            if user_orgs.exists():
                current_org = user_orgs.first()
        
        context['current_org'] = current_org
        context['user_organizations'] = user.organizations.all() if not user.is_superuser else None
        
        return context


class OrganizationPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Миксин для проверки прав доступа к организации
    """
    
    def test_func(self):
        user = self.request.user
        
        # Суперадмин имеет доступ ко всему
        if user.is_superuser:
            return True
        
        # Проверяем, есть ли у пользователя доступ к текущей организации
        current_org = getattr(user, 'current_organization', None)
        if not current_org:
            return False
        
        return user.organizations.filter(id=current_org.id).exists()
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        else:
            raise PermissionDenied("У вас нет доступа к этой организации")


def filter_by_organization(queryset, organization):
    """
    Универсальная функция для фильтрации queryset по организации
    """
    if not organization:
        return queryset
    
    # Пробуем разные поля для фильтрации
    organization_fields = [
        'organization',
        'student__organization', 
        'mentor__organization',
        'course__organization',
        'lead__organization',
        'payment__student__organization',
        'assignment__course__organization',
        'submission__student__organization',
        'grade__submission__student__organization',
        'category__organization',  # Для финансов
        'account__organization',   # Для финансов
    ]
    
    for field in organization_fields:
        try:
            filter_kwargs = {field: organization}
            return queryset.filter(**filter_kwargs)
        except:
            continue
    
    return queryset


def get_current_organization(user):
    """
    Получает текущую организацию пользователя
    """
    if user.is_superuser:
        return None
    
    # Сначала пробуем получить через UserCurrentOrganization
    try:
        from apps.organizations.models import UserCurrentOrganization
        current_org_relation = UserCurrentOrganization.objects.select_related('organization').get(user=user)
        return current_org_relation.organization
    except UserCurrentOrganization.DoesNotExist:
        pass
    
    # Если нет текущей организации, пробуем получить первую доступную через StaffMember
    try:
        from apps.organizations.models import StaffMember, StaffOrganizationAccess
        staff_member = StaffMember.objects.select_related('user').get(user=user)
        
        # Получаем активные доступы персонала
        access = StaffOrganizationAccess.objects.select_related('organization').filter(
            staff_member=staff_member,
            is_active=True
        ).first()
        
        if access:
            # Создаем UserCurrentOrganization для будущего использования
            from apps.organizations.models import UserCurrentOrganization
            UserCurrentOrganization.objects.update_or_create(
                user=user,
                defaults={'organization': access.organization}
            )
            return access.organization
        return None
    except StaffMember.DoesNotExist:
        return None
    except Exception:
        return None
