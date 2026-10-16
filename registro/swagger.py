"""
Definição da documentação OpenAPI 3.0 e views Swagger UI para o BatePonto.
Disponível em /docs e /docs/ com especificação em /docs/schema.json.
"""
from django.http import HttpResponse, JsonResponse


OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "BatePonto API — Reconhecimento Facial & Ponto Eletrônico",
        "version": "1.0.0",
        "description": (
            "API oficial do sistema **BatePonto**, plataforma inteligente de controle de ponto "
            "com reconhecimento biométrico facial em tempo real (Haar Cascade + LBPH) e auditoria de registros.\n\n"
            "### Funcionalidades Principais:\n"
            "- **Biometria em Tempo Real:** Consulta de status de identificação facial e streaming contínuo da webcam.\n"
            "- **Controle de Ponto:** Marcação de Entrada e Saída com proteção anti-spoofing e captura de snapshot comprobatório.\n"
            "- **Gestão de Dispositivo:** Liberação imediata do hardware físico da webcam do sistema operacional.\n"
            "- **Histórico e Auditoria:** Consulta e espelho de ponto dos últimos 30 dias com controle estrito de privacidade.\n"
            "- **Treinamento Biométrico:** Cadastro e amostragem de novos funcionários com retreinamento atômico do modelo."
        ),
        "contact": {
            "name": "Suporte BatePonto",
            "url": "http://127.0.0.1:8000/",
        },
    },
    "servers": [
        {
            "url": "/",
            "description": "Servidor Local BatePonto",
        }
    ],
    "tags": [
        {
            "name": "Biometria & Câmera",
            "description": "Detecção facial em tempo real, streaming de vídeo e controle de hardware da webcam",
        },
        {
            "name": "Registro de Ponto",
            "description": "Marcação de entradas/saídas biométricas e histórico dos últimos 30 dias",
        },
        {
            "name": "Gestão de Colaboradores",
            "description": "Cadastro e amostragem biométrica para treinamento do classificador facial",
        },
    ],
    "paths": {
        "/api/status-reconhecimento/": {
            "get": {
                "tags": ["Biometria & Câmera"],
                "summary": "Consulta o status do reconhecimento facial atual na câmera",
                "description": (
                    "Retorna em tempo real se a câmera detectou um colaborador cadastrado (`RECONHECIDO`), "
                    "um rosto não identificado (`DESCONHECIDO`) ou se não há faces enquadradas (`SEM_FACE`).\n\n"
                    "Quando um colaborador é reconhecido, a sessão web é temporariamente autorizada para "
                    "permitir o acesso seguro ao seu respectivo espelho de ponto."
                ),
                "operationId": "getStatusReconhecimento",
                "responses": {
                    "200": {
                        "description": "Status da detecção e identificação retornado com sucesso.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/StatusReconhecimentoResponse"
                                },
                                "examples": {
                                    "reconhecido": {
                                        "summary": "Colaborador reconhecido",
                                        "value": {
                                            "status": "RECONHECIDO",
                                            "funcionario": {
                                                "id": 1,
                                                "nome": "Matheus Assis",
                                                "cpf": "***.***.***-31",
                                                "foto_url": "/media/foto/ft_matheus.jpg",
                                                "confidence": 42.5
                                            }
                                        }
                                    },
                                    "desconhecido": {
                                        "summary": "Face não cadastrada",
                                        "value": {
                                            "status": "DESCONHECIDO",
                                            "funcionario": None
                                        }
                                    },
                                    "sem_face": {
                                        "summary": "Nenhuma face detectada",
                                        "value": {
                                            "status": "SEM_FACE",
                                            "funcionario": None
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/bater-ponto/": {
            "post": {
                "tags": ["Registro de Ponto"],
                "summary": "Registra batida de ponto com validação biométrica",
                "description": (
                    "Registra a marcação de ponto eletrônico (`ENTRADA` ou `SAIDA`) para o funcionário solicitado.\n\n"
                    "**Mecanismos de Segurança e Integridade:**\n"
                    "1. **Proteção Anti-spoofing:** Verifica se o colaborador solicitado corresponde à face atualmente identificada na câmera (a menos que a requisição seja feita por um administrador autenticado).\n"
                    "2. **Auditoria Fotográfica:** Captura automaticamente um snapshot em tempo real da câmera e salva vinculado ao registro.\n"
                    "3. **Liberação de Hardware:** Libera imediatamente a webcam física (`camera_detection.stop()`)."
                ),
                "operationId": "baterPonto",
                "requestBody": {
                    "required": True,
                    "description": "Identificador do funcionário e o tipo de batida desejada.",
                    "content": {
                        "application/json": {
                            "schema": {
                                "$ref": "#/components/schemas/BaterPontoRequest"
                            },
                            "examples": {
                                "entrada": {
                                    "summary": "Registro de Entrada (OI)",
                                    "value": {
                                        "funcionario_id": 1,
                                        "tipo": "ENTRADA"
                                    }
                                },
                                "saida": {
                                    "summary": "Registro de Saída (TCHAU)",
                                    "value": {
                                        "funcionario_id": 1,
                                        "tipo": "SAIDA"
                                    }
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Ponto registrado com sucesso.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/BaterPontoResponse"
                                },
                                "examples": {
                                    "sucesso_entrada": {
                                        "summary": "Entrada confirmada",
                                        "value": {
                                            "success": True,
                                            "registro": {
                                                "id": 15,
                                                "funcionario_id": 1,
                                                "funcionario": "Matheus Assis",
                                                "tipo": "ENTRADA",
                                                "data": "16/10/2026",
                                                "hora": "13:45:10"
                                            },
                                            "redirect_url": "/historico/1/?status=entrada_sucesso"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "400": {
                        "description": "Dados incompletos ou tipo inválido.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                "example": {"error": "Dados incompletos ou inválidos."}
                            }
                        }
                    },
                    "403": {
                        "description": "Rosto na câmera não corresponde ao colaborador solicitado.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                "example": {
                                    "error": "Operação não autorizada: o rosto atual na câmera não corresponde ao colaborador solicitado."
                                }
                            }
                        }
                    },
                    "404": {
                        "description": "Funcionário não encontrado.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                "example": {"error": "Funcionário não encontrado."}
                            }
                        }
                    },
                    "405": {
                        "description": "Método não permitido (esperado POST).",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                "example": {"error": "Método não permitido."}
                            }
                        }
                    },
                    "500": {
                        "description": "Erro interno ao processar a solicitação.",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/fechar-camera/": {
            "post": {
                "tags": ["Biometria & Câmera"],
                "summary": "Fecha o stream e libera a webcam física imediatamente",
                "description": (
                    "Interrompe o fluxo de captura de vídeo do OpenCV, libera o hardware da câmera física "
                    "no sistema operacional e limpa os dados em memória da última pessoa reconhecida."
                ),
                "operationId": "fecharCamera",
                "responses": {
                    "200": {
                        "description": "Câmera liberada com sucesso.",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/FecharCameraResponse"
                                },
                                "example": {
                                    "success": True,
                                    "camera_status": "closed"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/face_detection/": {
            "get": {
                "tags": ["Biometria & Câmera"],
                "summary": "Streaming de vídeo contínuo com reconhecimento facial (MJPEG)",
                "description": (
                    "Fornece o feed de vídeo contínuo no formato `multipart/x-mixed-replace; boundary=frame`. "
                    "Cada frame é processado pelo algoritmo Haar Cascade para detecção de rostos e "
                    "pelo modelo LBPH para reconhecimento em tempo real."
                ),
                "operationId": "streamCamera",
                "responses": {
                    "200": {
                        "description": "Stream de vídeo contínuo MJPEG.",
                        "content": {
                            "multipart/x-mixed-replace": {
                                "schema": {
                                    "type": "string",
                                    "format": "binary"
                                }
                            }
                        }
                    }
                }
            }
        },
        "/historico/{funcionario_id}/": {
            "get": {
                "tags": ["Registro de Ponto"],
                "summary": "Espelho de ponto dos últimos 30 dias do colaborador",
                "description": (
                    "Renderiza o espelho de ponto eletrônico do funcionário, contendo métricas consolidadas, "
                    "saldo de horas, dias trabalhados e agrupamento de registros por dia.\n\n"
                    "**Controle de Privacidade Estrito:** O acesso é permitido exclusivamente ao colaborador "
                    "reconhecido (com sessão temporária ativa) ou a administradores autenticados."
                ),
                "operationId": "getHistoricoFuncionario",
                "parameters": [
                    {
                        "name": "funcionario_id",
                        "in": "path",
                        "required": True,
                        "description": "ID numérico do funcionário.",
                        "schema": {"type": "integer"}
                    },
                    {
                        "name": "tipo",
                        "in": "query",
                        "required": False,
                        "description": "Filtro opcional pelo tipo de registro.",
                        "schema": {
                            "type": "string",
                            "enum": ["TODOS", "ENTRADA", "SAIDA"],
                            "default": "TODOS"
                        }
                    },
                    {
                        "name": "status",
                        "in": "query",
                        "required": False,
                        "description": "Feedback visual pós-batida (ex: entrada_sucesso, saida_sucesso).",
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "HTML da tela do espelho de ponto renderizado.",
                        "content": {"text/html": {}}
                    },
                    "302": {
                        "description": "Redirecionamento para a página inicial caso o acesso seja negado por privacidade."
                    }
                }
            }
        },
        "/historico/": {
            "get": {
                "tags": ["Registro de Ponto"],
                "summary": "Visão geral do histórico de 30 dias (Exclusivo Administrador)",
                "description": (
                    "Permite a gestores e administradores inspecionar a frequência de todos os funcionários "
                    "cadastrados, com seletor de colaboradores e métricas globais dos últimos 30 dias."
                ),
                "operationId": "getHistoricoGeral",
                "parameters": [
                    {
                        "name": "funcionario",
                        "in": "query",
                        "required": False,
                        "description": "ID do colaborador para redirecionamento direto.",
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "HTML da visão geral de histórico renderizado.",
                        "content": {"text/html": {}}
                    },
                    "302": {
                        "description": "Redirecionamento para login ou espelho de colaborador único."
                    }
                }
            }
        },
        "/cadastrar/": {
            "post": {
                "tags": ["Gestão de Colaboradores"],
                "summary": "Cadastra novo colaborador e retreina a base biométrica (Admin)",
                "description": (
                    "Cria um novo funcionário com nome, CPF e foto inicial de referência. "
                    "Aciona automaticamente o retreinamento do classificador LBPH em disco.\n\n"
                    "Acesso exclusivo para administradores autenticados."
                ),
                "operationId": "criarFuncionario",
                "requestBody": {
                    "required": True,
                    "description": "Dados cadastrais e foto de referência.",
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "required": ["nome", "cpf", "foto"],
                                "properties": {
                                    "nome": {"type": "string", "example": "Ana Clara Santos"},
                                    "cpf": {"type": "string", "example": "123.456.789-00"},
                                    "foto": {"type": "string", "format": "binary"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "302": {
                        "description": "Redireciona para o passo 2 de amostragem facial `/criar_coleta_faces/<id>`."
                    },
                    "200": {
                        "description": "Formulário com mensagens de validação em caso de erro."
                    }
                }
            }
        },
        "/criar_coleta_faces/{funcionario_id}": {
            "post": {
                "tags": ["Gestão de Colaboradores"],
                "summary": "Captura foto de amostragem facial via webcam e retreina o modelo (Admin)",
                "description": (
                    "Captura snapshot do colaborador posicionado na câmera guia e retreina atomicamente "
                    "o classificador biométrico LBPH para aumentar a precisão do reconhecimento."
                ),
                "operationId": "criarColetaFaces",
                "parameters": [
                    {
                        "name": "funcionario_id",
                        "in": "path",
                        "required": True,
                        "description": "ID do funcionário em processo de amostragem.",
                        "schema": {"type": "integer"}
                    }
                ],
                "responses": {
                    "302": {
                        "description": "Redireciona para a tela de conclusão `/sucesso/<funcionario_id>/`."
                    }
                }
            }
        }
    },
    "components": {
        "schemas": {
            "FuncionarioResumo": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 1},
                    "nome": {"type": "string", "example": "Matheus Assis"},
                    "cpf": {"type": "string", "example": "***.***.***-31"},
                    "foto_url": {"type": "string", "example": "/media/foto/ft_matheus.jpg"},
                    "confidence": {
                        "type": "number",
                        "format": "float",
                        "example": 42.5,
                        "description": "Distância de confiança calculada pelo algoritmo LBPH (valores menores indicam maior proximidade biométrica)."
                    }
                }
            },
            "StatusReconhecimentoResponse": {
                "type": "object",
                "required": ["status"],
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["RECONHECIDO", "DESCONHECIDO", "SEM_FACE"],
                        "example": "RECONHECIDO"
                    },
                    "funcionario": {
                        "nullable": True,
                        "allOf": [{"$ref": "#/components/schemas/FuncionarioResumo"}]
                    }
                }
            },
            "BaterPontoRequest": {
                "type": "object",
                "required": ["funcionario_id", "tipo"],
                "properties": {
                    "funcionario_id": {
                        "type": "integer",
                        "description": "ID do funcionário registrado no sistema.",
                        "example": 1
                    },
                    "tipo": {
                        "type": "string",
                        "enum": ["ENTRADA", "SAIDA"],
                        "description": "Tipo de batida de ponto.",
                        "example": "ENTRADA"
                    }
                }
            },
            "RegistroPontoItem": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "example": 15},
                    "funcionario_id": {"type": "integer", "example": 1},
                    "funcionario": {"type": "string", "example": "Matheus Assis"},
                    "tipo": {"type": "string", "enum": ["ENTRADA", "SAIDA"], "example": "ENTRADA"},
                    "data": {"type": "string", "example": "16/10/2026"},
                    "hora": {"type": "string", "example": "13:45:10"}
                }
            },
            "BaterPontoResponse": {
                "type": "object",
                "required": ["success", "registro", "redirect_url"],
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "registro": {"$ref": "#/components/schemas/RegistroPontoItem"},
                    "redirect_url": {
                        "type": "string",
                        "example": "/historico/1/?status=entrada_sucesso"
                    }
                }
            },
            "FecharCameraResponse": {
                "type": "object",
                "required": ["success", "camera_status"],
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "camera_status": {"type": "string", "example": "closed"}
                }
            },
            "ErrorResponse": {
                "type": "object",
                "required": ["error"],
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "Operação não autorizada: o rosto atual na câmera não corresponde ao colaborador solicitado."
                    }
                }
            }
        }
    }
}


def openapi_schema_view(request):
    """Retorna a especificação OpenAPI 3.0.3 em formato JSON."""
    return JsonResponse(OPENAPI_SPEC, json_dumps_params={'indent': 2, 'ensure_ascii': False})


def swagger_ui_view(request):
    """Renderiza a interface interativa do Swagger UI personalizada para o BatePonto."""
    html_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BatePonto API — Documentação Swagger</title>
    <link rel="icon" type="image/png" href="/static/img/favicon.png">
    
    <!-- Swagger UI CSS com fallback local/CDN -->
    <link rel="stylesheet" href="/static/swagger/swagger-ui.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
        * {
            box-sizing: border-box;
        }
        body {
            margin: 0;
            padding: 0;
            background: #F8FAFC;
            color: #1E293B;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        
        /* Barra de Topo Personalizada BatePonto */
        .header-bp {
            background-color: #0066FF;
            color: #ffffff;
            height: 56px;
            padding: 0 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .header-bp-brand {
            display: flex;
            align-items: center;
            gap: 12px;
            text-decoration: none;
            color: #ffffff;
            font-weight: 600;
            font-size: 1.05rem;
            letter-spacing: -0.01em;
        }
        .header-bp-brand img {
            width: 32px;
            height: 32px;
            border-radius: 8px;
            object-fit: contain;
            border: 1px solid rgba(255, 255, 255, 0.25);
            background: #0066FF;
        }
        .header-bp-badge {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 9999px;
            letter-spacing: 0.04em;
        }
        .header-bp-links {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .header-bp-links a {
            color: rgba(255, 255, 255, 0.9);
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 500;
            padding: 6px 12px;
            border-radius: 6px;
            transition: background 0.15s, color 0.15s;
        }
        .header-bp-links a:hover {
            color: #ffffff;
            background: rgba(255, 255, 255, 0.12);
        }
        .header-bp-links a.active {
            background: rgba(255, 255, 255, 0.2);
            color: #ffffff;
        }
        
        /* Ajustes e Customizações no Swagger UI */
        .swagger-ui .topbar {
            display: none !important;
        }
        .swagger-ui {
            max-width: 1200px;
            margin: 0 auto;
            padding: 24px 20px 48px;
        }
        .swagger-ui .info {
            margin: 16px 0 28px 0;
        }
        .swagger-ui .info .title {
            font-family: 'Inter', sans-serif;
            font-size: 2rem;
            color: #0F172A;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        .swagger-ui .info .description {
            font-family: 'Inter', sans-serif;
            color: #475569;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .swagger-ui .info .description h3 {
            color: #1E293B;
            margin-top: 18px;
            margin-bottom: 8px;
            font-size: 1.05rem;
        }
        
        /* Estilização de Métodos HTTP */
        .swagger-ui .opblock.opblock-post {
            border-color: #10B981;
            background: rgba(16, 185, 129, 0.04);
            border-radius: 8px;
        }
        .swagger-ui .opblock.opblock-post .opblock-summary-method {
            background: #10B981;
            font-weight: 600;
            border-radius: 5px;
        }
        .swagger-ui .opblock.opblock-get {
            border-color: #0066FF;
            background: rgba(0, 102, 255, 0.04);
            border-radius: 8px;
        }
        .swagger-ui .opblock.opblock-get .opblock-summary-method {
            background: #0066FF;
            font-weight: 600;
            border-radius: 5px;
        }
        .swagger-ui .btn.execute {
            background-color: #0066FF;
            border-color: #0066FF;
            color: #ffffff;
            font-weight: 600;
            border-radius: 6px;
            transition: opacity 0.15s;
        }
        .swagger-ui .btn.execute:hover {
            opacity: 0.9;
        }
        .swagger-ui .opblock-tag {
            font-family: 'Inter', sans-serif;
            color: #0F172A;
            border-bottom: 1px solid #E2E8F0;
            margin-top: 24px;
            font-size: 1.25rem;
            padding-bottom: 8px;
        }
    </style>
</head>
<body>
    <header class="header-bp">
        <a href="/" class="header-bp-brand">
            <img src="/static/img/logo.png" alt="Logo BatePonto">
            <span>BatePonto</span>
            <span class="header-bp-badge">Swagger / OpenAPI</span>
        </a>
        <nav class="header-bp-links">
            <a href="/">Terminal</a>
            <a href="/historico/">Registros</a>
            <a href="/docs/schema.json" target="_blank" class="active">JSON Schema</a>
        </nav>
    </header>

    <div id="swagger-ui"></div>

    <script src="/static/swagger/swagger-ui-bundle.js"></script>
    <script src="/static/swagger/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            window.ui = SwaggerUIBundle({
                url: "/docs/schema.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout",
                displayRequestDuration: true,
                defaultModelsExpandDepth: 2,
                docExpansion: "list",
                filter: true,
                showExtensions: true,
                showCommonExtensions: true,
                tryItOutEnabled: true
            });
        };
    </script>
</body>
</html>
"""
    return HttpResponse(html_content, content_type="text/html; charset=utf-8")
