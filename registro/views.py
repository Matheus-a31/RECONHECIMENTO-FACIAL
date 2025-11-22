from django.shortcuts import render, redirect
from .forms import FuncionarioForm, ColetaFacesForm
from .models import Funcionario, ColetaFaces

def criar_funcionario(request):
    if request.method == 'POST':
        form = FuncionarioForm(request.POST, request.FILES)
        if form.is_valid():
            funcionario = form.save()
            return redirect('criar_coleta_faces',
                            funcionario_id=funcionario.id)
    else:
        form = FuncionarioForm()
    return render(request, 
                  'criar_funcionario.html', 
                  {'form': form})
    
def criar_coleta_faces(request, funcionario_id):
    
    funcionario = Funcionario.objects.get(id=funcionario_id)
    
    if request.method == 'POST':
        form = ColetaFacesForm(request.POST, request.FILES)
        if form.is_valid():
            for foto in request.FILES.getlist('foto'):
                ColetaFaces.objects.create(funcionario=funcionario,
                                            foto=foto)
    else:
        form = ColetaFacesForm()
        
    context = {
        'funcionario': funcionario,
        'form': form
    }
    return render(request,
                  'criar_coleta_faces.html',
                  context)
