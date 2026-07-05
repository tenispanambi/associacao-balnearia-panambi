from django.contrib import admin

from .models import (
    Espaco,
    FotoEspaco,
    Cliente,
    Reserva,
    ConfiguracaoWhatsApp,
    RegraReserva,
)


# ==========================================================
# FOTOS DOS ESPAÇOS
# ==========================================================

class FotoEspacoInline(admin.TabularInline):
    model = FotoEspaco
    extra = 1
    max_num = 20


# ==========================================================
# ESPAÇOS
# ==========================================================

@admin.register(Espaco)
class EspacoAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'capacidade',
        'valor_socio',
        'caucao',
        'status',
    )

    list_filter = (
        'status',
        'wifi',
        'ar_condicionado',
        'churrasqueira',
    )

    search_fields = (
        'nome',
        'descricao',
    )

    inlines = [FotoEspacoInline]


# ==========================================================
# CLIENTES
# ==========================================================

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'nome',
        'telefone',
        'cpf',
        'socio',
    )

    search_fields = (
        'nome',
        'telefone',
        'cpf',
    )

    list_filter = (
        'socio',
    )


# ==========================================================
# RESERVAS
# ==========================================================

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        'data',
        'hora_inicio',
        'hora_fim',
        'espaco',
        'cliente',
        'status',
        'origem',
    )

    list_filter = (
        'status',
        'origem',
        'espaco',
        'periodo',
    )

    search_fields = (
        'cliente__nome',
        'cliente__telefone',
        'cliente__cpf',
        'espaco__nome',
    )

    autocomplete_fields = (
        'cliente',
        'espaco',
    )


# ==========================================================
# GALERIA DE FOTOS
# ==========================================================

@admin.register(FotoEspaco)
class FotoEspacoAdmin(admin.ModelAdmin):
    list_display = (
        'espaco',
        'legenda',
        'ordem',
    )

    list_filter = (
        'espaco',
    )

    search_fields = (
        'espaco__nome',
        'legenda',
    )

    ordering = (
        'espaco',
        'ordem',
    )


# ==========================================================
# CONFIGURAÇÕES DO WHATSAPP
# ==========================================================

@admin.register(ConfiguracaoWhatsApp)
class ConfiguracaoWhatsAppAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'contato_secretaria',
        'atualizado_em',
    )

    fieldsets = (

        ('Mensagem Inicial', {
            'fields': (
                'mensagem_boas_vindas',
            )
        }),

        ('Mensagens Automáticas', {
            'fields': (
                'mensagem_confirmacao',
                'mensagem_sem_disponibilidade',
                'mensagem_atendente',
            )
        }),

        ('Contato', {
            'fields': (
                'contato_secretaria',
            )
        }),

    )


# ==========================================================
# REGRAS DAS RESERVAS
# ==========================================================

@admin.register(RegraReserva)
class RegraReservaAdmin(admin.ModelAdmin):

    list_display = (
        'ordem',
        'titulo',
        'ativa',
        'obrigatoria',
    )

    list_editable = (
        'ativa',
        'obrigatoria',
    )

    ordering = (
        'ordem',
        'id',
    )

    search_fields = (
        'titulo',
        'texto',
    )