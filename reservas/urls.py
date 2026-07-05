from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('espacos/', views.espacos_lista, name='espacos_lista'),

    path('calendario/', views.calendario, name='calendario'),
    path('calendario/eventos/', views.calendario_eventos, name='calendario_eventos'),

    path('reservas/nova/', views.nova_reserva, name='nova_reserva'),

    path('solicitacoes/', views.solicitacoes, name='solicitacoes'),
    path('reservas/<int:reserva_id>/confirmar/', views.confirmar_reserva, name='confirmar_reserva'),
    path('reservas/<int:reserva_id>/cancelar/', views.cancelar_reserva, name='cancelar_reserva'),
    path('atendimento/', views.atendimento, name='atendimento'),
    path('atendimento/mensagem/', views.atendimento_mensagem, name='atendimento_mensagem'),
    path('espacos/novo/', views.espaco_criar, name='espaco_criar'),
    path('espacos/<int:espaco_id>/editar/', views.espaco_editar, name='espaco_editar'),
    path('espacos/<int:espaco_id>/deletar/', views.espaco_deletar, name='espaco_deletar'),
    path('espacos/foto/<int:pk>/excluir/', views.espaco_foto_excluir, name='espaco_foto_excluir'),
    path(    'reservas/<int:reserva_id>/excluir/', views.reserva_excluir, name='reserva_excluir'),
]