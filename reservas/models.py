from django.db import models


class Espaco(models.Model):
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('manutencao', 'Em manutenção'),
        ('inativo', 'Inativo'),
    ]

    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    capacidade = models.PositiveIntegerField(default=0)

    valor_socio = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    caucao = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fim = models.TimeField(null=True, blank=True)

    foto_capa = models.ImageField(
        upload_to='espacos/capas/',
        blank=True,
        null=True
    )

    churrasqueira = models.BooleanField(default=False)
    cozinha = models.BooleanField(default=False)
    freezer = models.BooleanField(default=False)
    geladeira = models.BooleanField(default=False)
    ar_condicionado = models.BooleanField(default=False)
    wifi = models.BooleanField(default=False)
    estacionamento = models.BooleanField(default=False)
    banheiros = models.BooleanField(default=False)

    regras = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Espaço'
        verbose_name_plural = 'Espaços'

    def __str__(self):
        return self.nome


class FotoEspaco(models.Model):
    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.CASCADE,
        related_name='fotos'
    )

    imagem = models.ImageField(upload_to='espacos/galeria/')
    legenda = models.CharField(max_length=150, blank=True)
    ordem = models.PositiveIntegerField(default=1)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ordem', 'id']
        verbose_name = 'Foto do Espaço'
        verbose_name_plural = 'Fotos dos Espaços'

    def __str__(self):
        return f'Foto - {self.espaco.nome}'


class Cliente(models.Model):
    nome = models.CharField(max_length=120)
    telefone = models.CharField(max_length=30, blank=True)
    cpf = models.CharField(max_length=20, blank=True)
    socio = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome


class Reserva(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Aguardando confirmação'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('finalizada', 'Finalizada'),
    ]

    ORIGEM_CHOICES = [
        ('manual', 'Manual'),
        ('whatsapp', 'WhatsApp'),
    ]

    TIPO_UTENSILIOS_CHOICES = [
        ('', 'Não informado'),
        ('mesas', 'Já deixar montado nas mesas'),
        ('buffet', 'Deixar tudo em uma mesa - sistema buffet'),
    ]

    TOALHAS_CHOICES = [
        ('', 'Não informado'),
        ('tnt', 'TNT brancas sem custo'),
        ('tecido', 'Tecido brancas + R$ 60,00 extra'),
    ]

    PERIODO_CHOICES = [
        ('meio_dia', 'Meio-dia'),
        ('tarde', 'Tarde'),
        ('noite', 'Noite'),
    ]

    espaco = models.ForeignKey(
        Espaco,
        on_delete=models.PROTECT,
        related_name='reservas'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='reservas'
    )

    data = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    quantidade_pessoas = models.PositiveIntegerField(default=0)
    observacoes = models.TextField(blank=True)

    decoracao = models.BooleanField(default=False)
    brinquedos_inflaveis = models.BooleanField(default=False)
    musica_ao_vivo = models.BooleanField(default=False)
    churrasqueira_rotativa = models.BooleanField(default=False)
    utensilios_vidro = models.BooleanField(default=False)

    tipo_utensilios = models.CharField(
        max_length=20,
        choices=TIPO_UTENSILIOS_CHOICES,
        blank=True,
        default=''
    )

    toalhas = models.CharField(
        max_length=20,
        choices=TOALHAS_CHOICES,
        blank=True,
        default=''
    )

    periodo = models.CharField(
        max_length=20,
        choices=PERIODO_CHOICES,
        blank=True,
        default='noite'
    )

    aceitou_regras = models.BooleanField(default=False)

    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default='manual'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data', '-hora_inicio']
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def __str__(self):
        return f'{self.data} - {self.espaco.nome} - {self.cliente.nome}'


class ConfiguracaoWhatsApp(models.Model):
    mensagem_boas_vindas = models.TextField(
        default='👋 Olá! Bem-vindo à Associação Balneária Panambi.'
    )

    mensagem_confirmacao = models.TextField(
        default='✅ Sua solicitação foi registrada com sucesso.'
    )

    mensagem_sem_disponibilidade = models.TextField(
        default='❌ Não há disponibilidade para esta data.'
    )

    mensagem_atendente = models.TextField(
        default='👩‍💼 Sua conversa será encaminhada para a secretaria. Aguarde atendimento.'
    )

    contato_secretaria = models.CharField(
        max_length=120,
        blank=True
    )

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuração do WhatsApp'
        verbose_name_plural = 'Configurações do WhatsApp'

    def __str__(self):
        return 'Configurações do WhatsApp'

    @classmethod
    def get_config(cls):
        config, created = cls.objects.get_or_create(id=1)
        return config


class RegraReserva(models.Model):
    titulo = models.CharField(max_length=150, blank=True)
    texto = models.TextField()
    ordem = models.PositiveIntegerField(default=1)
    ativa = models.BooleanField(default=True)
    obrigatoria = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['ordem', 'id']
        verbose_name = 'Regra da Reserva'
        verbose_name_plural = 'Regras da Reserva'

    def __str__(self):
        return self.titulo or self.texto[:50]