#  Sistema de Reconhecimento Facial Inteligente

![Python](https://img.shields.io/badge/Python-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![Django](https://img.shields.io/badge/Django-107C41?style=for-the-badge&logo=Django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-0078D6?style=for-the-badge&logo=OpenCV&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-107C41?style=for-the-badge&logo=Swagger&logoColor=white)

**Visão Geral:** Este projeto é um sistema web robusto para cadastro, coleta de faces e reconhecimento de funcionários em tempo real. Desenvolvido com **Python** (Django) para o backend e **OpenCV** para o processamento de imagens, a interface é moderna e responsiva, utilizando **Tailwind CSS**.


## Funcionalidades Principais

  * **Cadastro de Funcionários:** Formulário simples para registro de dados básicos (`nome`, `cpf`) e uma foto principal.
  * **Coleta de Faces:** Sistema de *upload* de múltiplas imagens (diferentes ângulos e iluminações) para treinar o algoritmo de reconhecimento com alta precisão.
  * **Reconhecimento em Tempo Real:** Interface para exibir o *stream* de vídeo da câmera, detectando e identificando faces conhecidas.
  * **Tecnologia Web Moderna:** Utilização de **Django Forms** customizados e **Tailwind CSS** para uma experiência de usuário agradável.

<img width="1612" height="777" alt="Screenshot 2026-10-16 at 13-45-24 Bater Ponto BatePonto" src="https://github.com/user-attachments/assets/81b124fe-c422-4953-bf4c-a0159d9dd756" />

<img width="1518" height="856" alt="Screenshot 2026-10-16 at 13-44-45 legal BatePonto" src="https://github.com/user-attachments/assets/83473af8-3b58-44bf-b798-b872aac3233f" />

<img width="1215" height="725" alt="Screenshot 2026-10-16 at 13-45-00 Novo Colaborador BatePonto" src="https://github.com/user-attachments/assets/eb0d0868-9f5a-44df-b447-7e254ab0c05c" />


## Tecnologias Utilizadas

| Categoria | Tecnologia | Uso |
| :--- | :--- | :--- |
| **Backend** | Python 3.x | Linguagem de programação principal. |
| **Framework Web** | Django (v5.x) | Estrutura web para gerenciamento de rotas, banco de dados (Models) e templates. |
| **Visão Computacional** | OpenCV | Detecção de faces, captura de vídeo e pré-processamento de imagens. |
| **Reconhecimento** | `face_recognition` | Implementação do algoritmo de aprendizado de máquina para identificação. |
| **Frontend/Estilo** | Tailwind CSS | Framework *utility-first* para design rápido e responsivo. |
| **Banco de Dados** | SQLite | Armazenamento de dados de funcionários e metadados de coleta. |
| **Documentação** | Swagger | Documentação das rotas da API na rota `/docs`|


## Configuração e Instalação

Siga os passos abaixo para configurar o projeto em seu ambiente local.

### 1\. Clonar o Repositório e Configurar o Ambiente Virtual

```bash
# Clone o projeto
git clone [https://github.com/Matheus-a31/RECONHECIMENTO-FACIAL.git]
cd RECONHECIMENTO-FACIAL

# Crie e ative o ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.\.venv\Scripts\activate    # Windows
```

### 2\. Instalar Dependências

Instale todas as bibliotecas Python necessárias (incluindo Django, OpenCV, etc.).

```bash
pip install -r requirements.txt
```

**(Certifique-se de criar o arquivo `requirements.txt` com todas as dependências\!)**

### 3\. Configurar Mídia e Banco de Dados

Crie o banco de dados e as migrações necessárias.

```bash
# Executa as migrações iniciais
python manage.py makemigrations registro
python manage.py migrate

# Cria um superusuário para acessar o painel Admin
python manage.py createsuperuser
```

**Configuração de Mídia (para Imagens):**

Certifique-se de que seu `settings.py` possui as configurações de mídia para que as fotos de funcionários sejam salvas e exibidas corretamente:

```python
# settings.py
import os
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

### 4\. Executar o Servidor

Inicie o servidor de desenvolvimento do Django:

```bash
python manage.py runserver
```

Acesse a aplicação em seu navegador: `http://127.0.0.1:8000/`



##  Fluxo de Uso do Sistema

1.  **Acesso Inicial:** Ao acessar a raiz (`/`), você será direcionado para o formulário de cadastro (`/criar/`).
2.  **Cadastro de Dados:** Preencha o Nome, CPF e carregue a Foto Principal do funcionário.
3.  **Coleta de Faces:** Após o cadastro, o sistema o redireciona para a página de coleta, onde você deve carregar múltiplos arquivos de imagem para aumentar a precisão do reconhecimento.
4.  **Treinamento (Próximo Passo):** Após a coleta, os dados devem ser processados por um script de treinamento para criar o modelo de reconhecimento.
5.  **Reconhecimento (Página Principal):** A página principal de reconhecimento exibirá o *stream* de vídeo com as caixas delimitadoras e o nome do funcionário detectado.



##  Contribuição

Contribuições, *issues* e pedidos de *features* são bem-vindos\! Sinta-se à vontade para verificar a [página de *issues*](https://www.google.com/).


##  Autor

  * **Matheus** - https://github.com/Matheus-a31 | https://www.linkedin.com/in/matheus-oliveira31


## Licença

Este projeto está licenciado sob a Licença MIT. Veja o arquivo `LICENSE` para mais detalhes.
