from datetime import datetime, time, timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import ProtectedError

from .models import (
    Espaco,
    FotoEspaco,
    Reserva,
    Cliente,
    ConfiguracaoWhatsApp,
    RegraReserva,
)

from .forms import EspacoForm


def home(request):
    total_espacos = Espaco.objects.count()
    pendentes = Reserva.objects.filter(status='pendente').count()
    confirmadas = Reserva.objects.filter(status='confirmada').count()

    proximas = Reserva.objects.select_related('cliente', 'espaco').exclude(
        status='cancelada'
    ).order_by('data', 'hora_inicio')[:6]

    return render(request, 'reservas/home.html', {
        'total_espacos': total_espacos,
        'pendentes': pendentes,
        'confirmadas': confirmadas,
        'proximas': proximas,
    })


def espacos_lista(request):
    espacos = Espaco.objects.all().order_by('nome')
    return render(request, 'reservas/espacos_lista.html', {'espacos': espacos})


def salvar_fotos_galeria(request, espaco):
    fotos = request.FILES.getlist('fotos_galeria')
    if not fotos:
        return
    total_atual = espaco.fotos.count()
    vagas = 5 - total_atual
    if vagas <= 0:
        messages.warning(request, 'Este espaço já possui o limite de 5 fotos na galeria.')
        return
    for foto in fotos[:vagas]:
        FotoEspaco.objects.create(espaco=espaco, imagem=foto)
    if len(fotos) > vagas:
        messages.warning(request, f'Foram salvas apenas {vagas} foto(s), pois o limite máximo é de 5 fotos.')


def mostrar_erros_formulario(request, form):
    for campo, erros in form.errors.items():
        nome_campo = campo
        if campo in form.fields:
            nome_campo = form.fields[campo].label or campo
        for erro in erros:
            messages.error(request, f'{nome_campo}: {erro}')


def espaco_criar(request):
    if request.method == 'POST':
        form = EspacoForm(request.POST, request.FILES)
        if form.is_valid():
            espaco = form.save()
            salvar_fotos_galeria(request, espaco)
            messages.success(request, 'Espaço cadastrado com sucesso.')
            return redirect('espacos_lista')
        mostrar_erros_formulario(request, form)
    else:
        form = EspacoForm()
    return render(request, 'reservas/espaco_form.html', {'form': form, 'titulo': 'Novo Espaço', 'espaco': None})


def espaco_editar(request, espaco_id):
    espaco = get_object_or_404(Espaco, id=espaco_id)
    if request.method == 'POST':
        form = EspacoForm(request.POST, request.FILES, instance=espaco)
        if form.is_valid():
            espaco = form.save()
            salvar_fotos_galeria(request, espaco)
            messages.success(request, 'Espaço atualizado com sucesso.')
            return redirect('espacos_lista')
        mostrar_erros_formulario(request, form)
    else:
        form = EspacoForm(instance=espaco)
    return render(request, 'reservas/espaco_form.html', {'form': form, 'titulo': 'Editar Espaço', 'espaco': espaco})


def espaco_foto_excluir(request, pk):
    foto = get_object_or_404(FotoEspaco, id=pk)
    espaco_id = foto.espaco.id
    if foto.imagem:
        foto.imagem.delete(save=False)
    foto.delete()
    messages.success(request, 'Foto removida com sucesso.')
    return redirect('espaco_editar', espaco_id=espaco_id)


def espaco_deletar(request, espaco_id):
    espaco = get_object_or_404(Espaco, id=espaco_id)
    if request.method == 'POST':
        try:
            espaco.delete()
            messages.success(request, 'Espaço excluído com sucesso.')
        except ProtectedError:
            messages.error(request, 'Este espaço possui reservas cadastradas e não pode ser excluído. Altere o status para Inativo.')
        return redirect('espacos_lista')
    return render(request, 'reservas/espaco_confirmar_delete.html', {'espaco': espaco})


def calendario(request):
    espacos = Espaco.objects.filter(status='ativo').order_by('nome')
    return render(request, 'reservas/calendario.html', {'espacos': espacos})


def calendario_eventos(request):
    espaco_id = request.GET.get('espaco')
    reservas = Reserva.objects.select_related('cliente', 'espaco').exclude(status='cancelada')
    if espaco_id:
        reservas = reservas.filter(espaco_id=espaco_id)
    eventos = []
    for reserva in reservas:
        cor = '#f59e0b' if reserva.status == 'pendente' else '#2563eb'
        inicio = datetime.combine(reserva.data, reserva.hora_inicio)
        fim = datetime.combine(reserva.data, reserva.hora_fim)
        if fim <= inicio:
            fim += timedelta(days=1)
        eventos.append({
            'id': reserva.id,
            'title': f'{reserva.cliente.nome} - {reserva.espaco.nome}',
            'start': inicio.isoformat(),
            'end': fim.isoformat(),
            'backgroundColor': cor,
            'borderColor': cor,
            'textColor': '#ffffff',
        })
    return JsonResponse(eventos, safe=False)


def nova_reserva(request):
    espacos = Espaco.objects.filter(status='ativo').order_by('nome')
    data_inicial = request.GET.get('data', '')
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        socio = request.POST.get('socio') == 'on'
        espaco_id = request.POST.get('espaco')
        data = request.POST.get('data')
        hora_inicio = request.POST.get('hora_inicio')
        hora_fim = request.POST.get('hora_fim')
        observacoes = request.POST.get('observacoes', '').strip()
        try:
            data_obj = datetime.strptime(data, '%Y-%m-%d').date()
            hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            hora_fim_obj = datetime.strptime(hora_fim, '%H:%M').time()
        except Exception:
            messages.error(request, 'Data ou horário inválido.')
            return redirect('nova_reserva')
        if tem_conflito_reserva(espaco_id, data_obj, hora_inicio_obj, hora_fim_obj):
            messages.error(request, 'Já existe uma reserva nesse espaço, data e horário.')
            return redirect('nova_reserva')
        cliente, criado = Cliente.objects.get_or_create(telefone=telefone, defaults={'nome': nome, 'socio': socio})
        if not criado:
            cliente.nome = nome
            cliente.socio = socio
            cliente.save()
        Reserva.objects.create(
            cliente=cliente,
            espaco_id=espaco_id,
            data=data,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            observacoes=observacoes,
            status='pendente',
            origem='manual',
            aceitou_regras=True,
        )
        messages.success(request, 'Reserva criada como aguardando confirmação.')
        return redirect('solicitacoes')
    return render(request, 'reservas/nova_reserva.html', {'espacos': espacos, 'data_inicial': data_inicial})


def solicitacoes(request):
    reservas = Reserva.objects.select_related('cliente', 'espaco').filter(status='pendente').order_by('data', 'hora_inicio')
    return render(request, 'reservas/solicitacoes.html', {'reservas': reservas})


def confirmar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    reserva.status = 'confirmada'
    reserva.save()
    messages.success(request, 'Reserva confirmada com sucesso.')
    return redirect('solicitacoes')


def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    reserva.status = 'cancelada'
    reserva.save()
    messages.success(request, 'Reserva cancelada.')
    return redirect('solicitacoes')


@require_POST
def reserva_excluir(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    reserva.delete()
    messages.success(request, 'Reserva excluída com sucesso.')
    return redirect('calendario')

# ==========================================================
# FUNÇÕES AUXILIARES DO WHATSAPP
# ==========================================================

def atendimento(request):
    request.session['chat_estado'] = {'etapa': 'inicio'}
    espacos = Espaco.objects.filter(status='ativo').order_by('nome')
    return render(request, 'reservas/atendimento.html', {'espacos': espacos})


def formatar_moeda(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def listar_estrutura(espaco):
    estrutura = []
    if espaco.churrasqueira:
        estrutura.append('🔥 Churrasqueira')
    if espaco.cozinha:
        estrutura.append('🍳 Cozinha')
    if espaco.freezer:
        estrutura.append('🧊 Freezer')
    if espaco.geladeira:
        estrutura.append('❄️ Geladeira')
    if espaco.ar_condicionado:
        estrutura.append('🌬️ Ar-condicionado')
    if espaco.wifi:
        estrutura.append('📶 Wi-Fi')
    if espaco.estacionamento:
        estrutura.append('🚗 Estacionamento')
    if espaco.banheiros:
        estrutura.append('🚻 Banheiros')
    return '\n'.join(estrutura) if estrutura else 'Não informado'


def menu_whatsapp():
    config = ConfiguracaoWhatsApp.get_config()
    return (
        f'{config.mensagem_boas_vindas}\n\n'
        'Como posso ajudar?\n\n'
        '1️⃣ Fazer reserva\n'
        '2️⃣ Conhecer os salões\n'
        '3️⃣ Consultar minha reserva\n'
        '4️⃣ Falar com a secretaria'
    )


def texto_regras_reserva():
    regras = RegraReserva.objects.filter(ativa=True).order_by('ordem', 'id')
    if not regras.exists():
        return (
            '📋 Regras da Reserva\n\n'
            'Nenhuma regra cadastrada no momento.\n\n'
            'Você aceita as regras da reserva?\n\n'
            '1️⃣ Sim\n'
            '2️⃣ Não'
        )
    texto = '📋 Regras da Reserva\n\n'
    for regra in regras:
        texto += f'• {regra.texto}\n'
    texto += '\nVocê aceita as regras para finalizar a solicitação?\n\n1️⃣ Sim\n2️⃣ Não'
    return texto


def menu_voltar_salao():
    return '\n0️⃣ Voltar às opções do salão\n9️⃣ Voltar ao menu principal'


def menu_opcoes_salao(espaco):
    return (
        f'🏛️ {espaco.nome}\n\n'
        'O que deseja fazer?\n\n'
        '1️⃣ Ver fotos\n'
        '2️⃣ Ver estrutura\n'
        '3️⃣ Ver valores e regras\n'
        '4️⃣ Reservar este salão\n'
        '5️⃣ Ver outro salão\n'
        '0️⃣ Voltar ao menu principal'
    )


def texto_detalhes_salao(espaco):
    resposta = f'🏛️ {espaco.nome}\n\n👥 Capacidade: {espaco.capacidade} pessoas\n\n'
    if espaco.descricao:
        resposta += f'📝 Descrição:\n{espaco.descricao}\n\n'
    resposta += menu_opcoes_salao(espaco)
    return resposta


def menu_horario_inicio():
    return (
        '⏰ Qual o horário de início do evento?\n\n'
        'Digite no formato HH:MM.\n\n'
        'Exemplos:\n'
        '09:00\n'
        '14:30\n'
        '18:00\n'
        '19:00\n\n'
        '0️⃣ Voltar ao menu principal'
    )


def menu_horario_fim():
    return (
        '⏰ Até que horas pretende utilizar o salão?\n\n'
        'Digite no formato HH:MM.\n\n'
        'Exemplos:\n'
        '23:00\n'
        '00:30\n'
        '01:00\n'
        '02:00\n\n'
        '0️⃣ Voltar ao menu principal'
    )


def menu_tipo_evento():
    return (
        '🎉 Qual será o tipo do evento?\n\n'
        '1️⃣ Aniversário\n'
        '2️⃣ Casamento\n'
        '3️⃣ Formatura\n'
        '4️⃣ Reunião\n'
        '5️⃣ Confraternização\n'
        '6️⃣ Outro\n\n'
        '0️⃣ Voltar ao menu principal'
    )


def parse_horario(texto):
    texto = texto.strip().replace('h', ':').replace('H', ':')
    if ':' not in texto:
        texto = f'{texto}:00'
    try:
        return datetime.strptime(texto, '%H:%M').time()
    except Exception:
        return None


def minutos_do_dia(hora):
    return hora.hour * 60 + hora.minute


def intervalo_normalizado(hora_inicio, hora_fim):
    inicio = minutos_do_dia(hora_inicio)
    fim = minutos_do_dia(hora_fim)
    if fim <= inicio:
        fim += 24 * 60
    return inicio, fim


def intervalos_sobrepoem(inicio_a, fim_a, inicio_b, fim_b):
    return inicio_a < fim_b and fim_a > inicio_b


def tem_conflito_reserva(espaco_id, data, hora_inicio, hora_fim):
    novo_inicio, novo_fim = intervalo_normalizado(hora_inicio, hora_fim)
    reservas = Reserva.objects.filter(
        espaco_id=espaco_id,
        data=data,
        status__in=['pendente', 'confirmada']
    )
    for reserva in reservas:
        atual_inicio, atual_fim = intervalo_normalizado(reserva.hora_inicio, reserva.hora_fim)
        if intervalos_sobrepoem(novo_inicio, novo_fim, atual_inicio, atual_fim):
            return True
    return False


def voltar_menu_principal():
    return menu_whatsapp(), {'etapa': 'menu_principal'}


# ==========================================================
# ATENDIMENTO WHATSAPP
# ==========================================================

@require_POST
def atendimento_mensagem(request):
    texto = request.POST.get('mensagem', '').strip()
    estado = request.session.get('chat_estado', {'etapa': 'inicio'})
    resposta = ''

    if estado.get('etapa') == 'inicio':
        resposta = menu_whatsapp()
        estado = {'etapa': 'menu_principal'}

    elif estado.get('etapa') == 'menu_principal':
        if texto == '1':
            resposta = '📅 Informe a data desejada para a reserva no formato DD/MM/AAAA.\n\n0️⃣ Voltar ao menu principal'
            estado = {'etapa': 'data_reserva'}
        elif texto == '2':
            espacos = Espaco.objects.filter(status='ativo').order_by('nome')
            if not espacos.exists():
                resposta = 'No momento não há salões ativos cadastrados.'
                estado = {'etapa': 'fim'}
            else:
                resposta = '🏛️ Escolha um salão para ver detalhes:\n\n'
                for i, espaco in enumerate(espacos, start=1):
                    resposta += f'{i}️⃣ {espaco.nome}\n👥 Capacidade: {espaco.capacidade} pessoas\n\n'
                resposta += '0️⃣ Voltar ao menu principal'
                estado = {'etapa': 'ver_salao'}
        elif texto == '3':
            resposta = 'Informe o número da reserva ou telefone usado na solicitação.\n\n0️⃣ Voltar ao menu principal'
            estado = {'etapa': 'consultar_reserva'}
        elif texto == '4':
            config = ConfiguracaoWhatsApp.get_config()
            resposta = config.mensagem_atendente
            if config.contato_secretaria:
                resposta += f'\n\nContato: {config.contato_secretaria}'
            resposta += '\n\nDigite qualquer mensagem para voltar ao menu.'
            estado = {'etapa': 'fim'}
        else:
            resposta = 'Opção inválida. Digite 1, 2, 3 ou 4.'

    elif estado.get('etapa') == 'ver_salao':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            espacos = list(Espaco.objects.filter(status='ativo').order_by('nome'))
            try:
                indice = int(texto) - 1
                espaco = espacos[indice]
            except Exception:
                resposta = 'Opção inválida. Digite o número do salão ou 0 para voltar.'
            else:
                resposta = texto_detalhes_salao(espaco)
                estado = {'etapa': 'opcoes_salao', 'espaco_info_id': espaco.id}

    elif estado.get('etapa') == 'opcoes_salao':
        espaco = get_object_or_404(Espaco, id=estado.get('espaco_info_id'))
        if texto == '1':
            fotos = []
            if espaco.foto_capa:
                fotos.append(('Foto de capa', espaco.foto_capa.url))
            for foto in espaco.fotos.all():
                fotos.append((foto.legenda or 'Foto do salão', foto.imagem.url))
            if not fotos:
                resposta = f'📷 {espaco.nome}\n\nEste salão ainda não possui fotos cadastradas.\n{menu_voltar_salao()}'
            else:
                resposta = f'📷 Fotos de {espaco.nome}\n\n'
                for i, item in enumerate(fotos, start=1):
                    legenda, url = item
                    resposta += f'{i}. {legenda}\n{url}\n\n'
                resposta += menu_voltar_salao()
            estado['etapa'] = 'voltar_opcoes_salao'
        elif texto == '2':
            resposta = f'✅ Estrutura de {espaco.nome}\n\n{listar_estrutura(espaco)}\n{menu_voltar_salao()}'
            estado['etapa'] = 'voltar_opcoes_salao'
        elif texto == '3':
            resposta = (
                f'💰 Valores e regras de {espaco.nome}\n\n'
                f'Valor sócio: {formatar_moeda(espaco.valor_socio)}\n'
                f'Caução: {formatar_moeda(espaco.caucao)}\n\n'
                f'📋 Regras específicas:\n'
                f'{espaco.regras if espaco.regras else "Não há regras específicas cadastradas para este salão."}\n'
                f'{menu_voltar_salao()}'
            )
            estado['etapa'] = 'voltar_opcoes_salao'
        elif texto == '4':
            estado['espaco_id'] = estado.get('espaco_info_id')
            estado['etapa'] = 'data_reserva'
            resposta = f'Você escolheu:\n\n🏛️ {espaco.nome}\n\nAgora informe a data desejada no formato DD/MM/AAAA.\n\n0️⃣ Voltar ao menu principal'
        elif texto == '5':
            espacos = Espaco.objects.filter(status='ativo').order_by('nome')
            resposta = '🏛️ Escolha outro salão:\n\n'
            for i, outro_espaco in enumerate(espacos, start=1):
                resposta += f'{i}️⃣ {outro_espaco.nome}\n👥 Capacidade: {outro_espaco.capacidade} pessoas\n\n'
            resposta += '0️⃣ Voltar ao menu principal'
            estado['etapa'] = 'ver_salao'
        elif texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            resposta = 'Opção inválida. Digite 1, 2, 3, 4, 5 ou 0.'

    elif estado.get('etapa') == 'voltar_opcoes_salao':
        if texto == '9':
            resposta, estado = voltar_menu_principal()
        else:
            espaco = get_object_or_404(Espaco, id=estado.get('espaco_info_id'))
            resposta = menu_opcoes_salao(espaco)
            estado['etapa'] = 'opcoes_salao'

    elif estado.get('etapa') == 'data_reserva':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            try:
                data = datetime.strptime(texto, '%d/%m/%Y').date()
            except Exception:
                resposta = 'Data inválida. Digite no formato DD/MM/AAAA.\n\n0️⃣ Voltar ao menu principal'
            else:
                estado['data'] = data.isoformat()
                if estado.get('espaco_id'):
                    espaco = get_object_or_404(Espaco, id=estado['espaco_id'])
                    estado['etapa'] = 'hora_inicio'
                    resposta = f'✅ Data informada: {data.strftime("%d/%m/%Y")}\n🏛️ Salão: {espaco.nome}\n\n{menu_horario_inicio()}'
                else:
                    espacos_ocupados = Reserva.objects.filter(data=data, status__in=['pendente', 'confirmada']).values_list('espaco_id', flat=True)
                    espacos = Espaco.objects.filter(status='ativo').exclude(id__in=espacos_ocupados).order_by('nome')
                    if not espacos.exists():
                        config = ConfiguracaoWhatsApp.get_config()
                        resposta = f'{config.mensagem_sem_disponibilidade}\n\nDigite outra data.\n\n0️⃣ Voltar ao menu principal'
                    else:
                        resposta = f'✅ Salões disponíveis em {data.strftime("%d/%m/%Y")}:\n\n'
                        for i, espaco in enumerate(espacos, start=1):
                            resposta += f'{i}️⃣ {espaco.nome}\n👥 Capacidade: {espaco.capacidade} pessoas\n💰 Valor sócio: {formatar_moeda(espaco.valor_socio)}\n\n'
                        resposta += '0️⃣ Voltar ao menu principal'
                        estado['etapa'] = 'escolher_espaco_disponivel'

    elif estado.get('etapa') == 'escolher_espaco_disponivel':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            data = datetime.fromisoformat(estado['data']).date()
            espacos_ocupados = Reserva.objects.filter(data=data, status__in=['pendente', 'confirmada']).values_list('espaco_id', flat=True)
            espacos = list(Espaco.objects.filter(status='ativo').exclude(id__in=espacos_ocupados).order_by('nome'))
            try:
                indice = int(texto) - 1
                espaco = espacos[indice]
            except Exception:
                resposta = 'Opção inválida. Digite o número do salão ou 0 para voltar ao menu.'
            else:
                estado['espaco_id'] = espaco.id
                estado['etapa'] = 'hora_inicio'
                resposta = f'🏛️ {espaco.nome}\n📅 Data: {data.strftime("%d/%m/%Y")}\n\n{menu_horario_inicio()}'

    elif estado.get('etapa') == 'hora_inicio':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            hora_inicio = parse_horario(texto)

            if not hora_inicio:
                resposta = (
                    '❌ Horário inválido.\n\n'
                    'Digite no formato HH:MM.\n\n'
                    'Exemplo: 19:30\n\n'
                    '0️⃣ Voltar ao menu principal'
                )
            else:
                estado['hora_inicio'] = hora_inicio.strftime('%H:%M')
                estado['etapa'] = 'hora_fim'
                resposta = menu_horario_fim()

    elif estado.get('etapa') == 'hora_fim':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            hora_fim = parse_horario(texto)

            if not hora_fim:
                resposta = (
                    '❌ Horário inválido.\n\n'
                    'Digite no formato HH:MM.\n\n'
                    'Exemplo: 01:00\n\n'
                    '0️⃣ Voltar ao menu principal'
                )
            else:
                hora_inicio = parse_horario(estado['hora_inicio'])
                data = datetime.fromisoformat(estado['data']).date()

                if tem_conflito_reserva(estado['espaco_id'], data, hora_inicio, hora_fim):
                    resposta = (
                        '❌ Já existe uma reserva ou solicitação nesse horário.\n\n'
                        'Informe outro horário de início.\n\n'
                        + menu_horario_inicio()
                    )
                    estado['etapa'] = 'hora_inicio'
                else:
                    estado['hora_fim'] = hora_fim.strftime('%H:%M')
                    estado['etapa'] = 'quantidade'
                    resposta = (
                        '👥 Quantas pessoas aproximadamente participarão?\n\n'
                        '0️⃣ Voltar ao menu principal'
                    )

    elif estado.get('etapa') == 'quantidade':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            try:
                estado['quantidade'] = int(texto)
                estado['etapa'] = 'tipo_evento'
                resposta = menu_tipo_evento()
            except Exception:
                resposta = 'Digite apenas o número de pessoas ou 0 para voltar.'

    elif estado.get('etapa') == 'tipo_evento':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            tipos = {'1': 'Aniversário', '2': 'Casamento', '3': 'Formatura', '4': 'Reunião', '5': 'Confraternização'}
            if texto in tipos:
                estado['tipo_evento'] = tipos[texto]
                estado['etapa'] = 'nome'
                resposta = 'Informe seu nome completo.\n\n0️⃣ Voltar ao menu principal'
            elif texto == '6':
                estado['etapa'] = 'tipo_evento_outro'
                resposta = 'Digite o tipo do evento.\n\nExemplo: Batizado, reunião familiar, jantar etc.\n\n0️⃣ Voltar ao menu principal'
            else:
                resposta = 'Opção inválida.\n\n' + menu_tipo_evento()

    elif estado.get('etapa') == 'tipo_evento_outro':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            estado['tipo_evento'] = texto
            estado['etapa'] = 'nome'
            resposta = 'Informe seu nome completo.\n\n0️⃣ Voltar ao menu principal'

    elif estado.get('etapa') == 'nome':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            estado['nome'] = texto
            estado['etapa'] = 'telefone'
            resposta = 'Informe seu telefone/WhatsApp.\n\n0️⃣ Voltar ao menu principal'

    elif estado.get('etapa') == 'telefone':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            estado['telefone'] = texto
            estado['etapa'] = 'socio'
            resposta = 'Você é sócio da Associação Balneária?\n\n1️⃣ Sim\n2️⃣ Não\n\n0️⃣ Voltar ao menu principal'

    elif estado.get('etapa') == 'socio':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        elif texto == '1':
            estado['socio'] = True
            estado['etapa'] = 'observacoes'
            resposta = 'Alguma observação? Se não tiver, digite "não".\n\n0️⃣ Voltar ao menu principal'
        elif texto == '2':
            resposta = '⚠️ As reservas dos salões são permitidas somente para sócios.\n\nPara mais informações, fale com a secretaria.\n\nDigite qualquer mensagem para voltar ao menu.'
            estado = {'etapa': 'fim'}
        else:
            resposta = 'Opção inválida. Digite 1 para Sim, 2 para Não ou 0 para voltar.'

    elif estado.get('etapa') == 'observacoes':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            estado['observacoes'] = texto
            estado['etapa'] = 'confirmar_resumo'
            espaco = get_object_or_404(Espaco, id=estado['espaco_id'])
            data_formatada = datetime.fromisoformat(estado['data']).strftime('%d/%m/%Y')
            resposta = (
                '✅ Confira sua solicitação\n\n'
                f'🏛️ Salão: {espaco.nome}\n'
                f'📅 Data: {data_formatada}\n'
                f'⏰ Horário: {estado["hora_inicio"]} até {estado["hora_fim"]}\n'
                f'🎉 Evento: {estado.get("tipo_evento", "Não informado")}\n'
                f'👥 Pessoas: {estado["quantidade"]}\n'
                f'👤 Nome: {estado["nome"]}\n'
                f'📱 Telefone: {estado["telefone"]}\n'
                f'💰 Valor sócio: {formatar_moeda(espaco.valor_socio)}\n'
                f'💵 Caução: {formatar_moeda(espaco.caucao)}\n\n'
                f'📝 Observações: {estado.get("observacoes")}\n\n'
                'Os dados estão corretos?\n\n'
                '1️⃣ Sim, continuar\n'
                '2️⃣ Cancelar\n'
                '0️⃣ Voltar ao menu principal'
            )

    elif estado.get('etapa') == 'confirmar_resumo':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        elif texto == '1':
            estado['etapa'] = 'aceitar_regras'
            resposta = texto_regras_reserva() + '\n\n0️⃣ Voltar ao menu principal'
        elif texto == '2':
            resposta = '❌ Solicitação cancelada. Para iniciar novamente, envie qualquer mensagem.'
            estado = {'etapa': 'fim'}
        else:
            resposta = 'Opção inválida. Digite 1 para continuar, 2 para cancelar ou 0 para voltar.'

    elif estado.get('etapa') == 'aceitar_regras':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        elif texto == '1':
            cliente, criado = Cliente.objects.get_or_create(telefone=estado['telefone'], defaults={'nome': estado['nome'], 'socio': True})
            if not criado:
                cliente.nome = estado['nome']
                cliente.socio = True
                cliente.save()
            hora_inicio = parse_horario(estado['hora_inicio'])
            hora_fim = parse_horario(estado['hora_fim'])
            data = datetime.fromisoformat(estado['data']).date()
            if tem_conflito_reserva(estado['espaco_id'], data, hora_inicio, hora_fim):
                resposta = '❌ Enquanto você preenchia, esse horário ficou indisponível.\n\nEscolha outro horário de início.\n\n' + menu_horario_inicio()
                estado['etapa'] = 'hora_inicio'
            else:
                observacoes_completas = f'Tipo do evento: {estado.get("tipo_evento", "Não informado")}\nObservações: {estado.get("observacoes", "")}'
                reserva = Reserva.objects.create(
                    cliente=cliente,
                    espaco_id=estado['espaco_id'],
                    data=estado['data'],
                    hora_inicio=hora_inicio,
                    hora_fim=hora_fim,
                    quantidade_pessoas=estado['quantidade'],
                    observacoes=observacoes_completas,
                    origem='whatsapp',
                    status='pendente',
                    aceitou_regras=True,
                    periodo='noite',
                )
                config = ConfiguracaoWhatsApp.get_config()
                resposta = (
                    f'{config.mensagem_confirmacao}\n\n'
                    f'🔖 Número da reserva: #{reserva.id}\n'
                    f'📅 Data: {reserva.data.strftime("%d/%m/%Y")}\n'
                    f'⏰ Horário: {reserva.hora_inicio.strftime("%H:%M")} até {reserva.hora_fim.strftime("%H:%M")}\n'
                    '📌 Status: 🟡 Aguardando confirmação\n\n'
                    'A secretaria irá analisar e confirmar pelo WhatsApp.'
                )
                estado = {'etapa': 'fim'}
        elif texto == '2':
            resposta = '❌ Para finalizar a solicitação é necessário aceitar as regras.\n\nDigite qualquer mensagem para voltar ao menu.'
            estado = {'etapa': 'fim'}
        else:
            resposta = 'Opção inválida. Digite 1 para aceitar, 2 para não aceitar ou 0 para voltar.'

    elif estado.get('etapa') == 'consultar_reserva':
        if texto == '0':
            resposta, estado = voltar_menu_principal()
        else:
            busca = texto.strip()
            reservas = Reserva.objects.select_related('cliente', 'espaco').filter(cliente__telefone__icontains=busca).exclude(status='cancelada').order_by('-data')[:5]
            if busca.isdigit():
                reservas_por_id = Reserva.objects.select_related('cliente', 'espaco').filter(id=busca)
                if reservas_por_id.exists():
                    reservas = reservas_por_id
            if not reservas:
                resposta = '❌ Não encontrei reserva com essa informação.\n\nDigite qualquer mensagem para voltar ao menu.'
            else:
                resposta = '📅 Reservas encontradas:\n\n'
                for reserva in reservas:
                    status = dict(Reserva.STATUS_CHOICES).get(reserva.status, reserva.status)
                    resposta += (
                        f'🔖 Reserva #{reserva.id}\n'
                        f'🏛️ Salão: {reserva.espaco.nome}\n'
                        f'📅 Data: {reserva.data.strftime("%d/%m/%Y")}\n'
                        f'⏰ Horário: {reserva.hora_inicio.strftime("%H:%M")} até {reserva.hora_fim.strftime("%H:%M")}\n'
                        f'📌 Status: {status}\n\n'
                    )
                resposta += 'Digite qualquer mensagem para voltar ao menu.'
            estado = {'etapa': 'fim'}

    elif estado.get('etapa') == 'fim':
        resposta = menu_whatsapp()
        estado = {'etapa': 'menu_principal'}

    else:
        resposta = menu_whatsapp()
        estado = {'etapa': 'menu_principal'}

    request.session['chat_estado'] = estado
    return JsonResponse({'resposta': resposta})
