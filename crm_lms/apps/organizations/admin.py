from django.contrib import admin
from django.forms import ModelForm
from .models import Organization, OrganizationMember, UserCurrentOrganization, StaffMember, StaffOrganizationAccess


class OrganizationAdminForm(ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Only for new objects
            # Generate next available code
            last_org = Organization.objects.order_by('-code').first()
            if last_org and last_org.code.isdigit():
                next_code = int(last_org.code) + 1
            else:
                next_code = 84  # Start from 0084
            self.fields['code'].initial = f"{next_code:04d}"
            self.fields['code'].widget.attrs['readonly'] = True


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    form = OrganizationAdminForm
    list_display = ['code', 'name', 'slug', 'is_active', 'created_at', 'members_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description', 'code']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'code')
        }),
        ('Дополнительно', {
            'fields': ('description', 'logo', 'is_active'),
            'classes': ('collapse',)
        }),
        ('Время', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def members_count(self, obj):
        return obj.members.count()
    members_count.short_description = 'Участников'


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'user__email', 'organization__name']
    readonly_fields = ['joined_at']


@admin.register(UserCurrentOrganization)
class UserCurrentOrganizationAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['user__username', 'organization__name']
    readonly_fields = ['updated_at']


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'created_by', 'organizations_count']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at']
    
    def organizations_count(self, obj):
        return obj.organizations.count()
    organizations_count.short_description = 'Организаций'


@admin.register(StaffOrganizationAccess)
class StaffOrganizationAccessAdmin(admin.ModelAdmin):
    list_display = ['staff_member', 'organization', 'is_active', 'granted_at', 'granted_by']
    list_filter = ['is_active', 'granted_at']
    search_fields = ['staff_member__user__username', 'organization__name']
    readonly_fields = ['granted_at']
