from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from random import randint


class Funcionario(models.Model):
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    foto = models.ImageField(upload_to='foto/')
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=20)
    
    def __str__(self):
        return self.nome

    def save(self, *args, **kwargs):
        if not self.slug:
            seq = self.nome + '_FUNC' + str(randint(1000000, 9999999))
            self.slug = slugify(seq)
        super().save(*args, **kwargs)

    
    
class ColetaFaces(models.Model):
    funcionario = models.ForeignKey(Funcionario, 
                                    on_delete=models.CASCADE, related_name='funcionario_coletas')
    foto = models.ImageField(upload_to='coleta/')
    

class Treinamento(models.Model):
    modelo = models.FileField(upload_to='treinamento/')
    
    class Meta:
        verbose_name = 'Treinamento'
        verbose_name_plural = 'Treinamentos'
        
        
    def __str__(self):
        return 'Classificador (frontalface)'
    
    def clean(self):
        model = self.__class__
        if model.objects.exclude(id=self.id).exists():
            raise ValidationError('Só pode existir um arquivo salvo. Por favor, exclua o outro primeiro.')


class RegistroPonto(models.Model):
    TIPO_CHOICES = (
        ('ENTRADA', 'Entrada'),
        ('SAIDA', 'Saída'),
    )
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='pontos')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    data = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    foto_registro = models.ImageField(upload_to='pontos/', null=True, blank=True)

    class Meta:
        verbose_name = 'Registro de Ponto'
        verbose_name_plural = 'Registros de Pontos'
        ordering = ['-data', '-hora']

    def __str__(self):
        return f"{self.funcionario.nome} - {self.tipo} ({self.data} {self.hora.strftime('%H:%M:%S')})"

        
    

    