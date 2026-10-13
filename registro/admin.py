from django.contrib import admin
from registro.models import (Funcionario, ColetaFaces, Treinamento, RegistroPonto)

class ColetaFacesInline(admin.TabularInline):
    model = ColetaFaces
    extra = 0

class FuncionarioAdmin(admin.ModelAdmin):
    readonly_fields = ['slug']
    inlines = (ColetaFacesInline,)
    
admin.site.register(Funcionario, FuncionarioAdmin)
admin.site.register(Treinamento)

class RegistroPontoAdmin(admin.ModelAdmin):
    list_display = ('funcionario', 'tipo', 'data', 'hora')
    list_filter = ('tipo', 'data')
    search_fields = ('funcionario__nome', 'funcionario__cpf')

admin.site.register(RegistroPonto, RegistroPontoAdmin)

