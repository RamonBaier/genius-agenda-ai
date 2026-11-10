# Genius Agenda AI

Assistente pessoal no WhatsApp que gerencia o Google Agenda por linguagem natural
(criar, consultar, alterar e excluir eventos) e envia lembretes automáticos.

## Arquitetura

```
WhatsApp ──► Evolution API ──webhook──► n8n (agente Gemini) ──► Google Calendar
                  ▲                          │
                  └────── sendText ◄─────────┤
                                             └──► Serviço Python + Postgres
                                                  (idempotência e lembretes)
```

| Componente | Função |
|---|---|
| Evolution API | Conecta o WhatsApp e envia/recebe mensagens |
| n8n | Orquestra o fluxo e hospeda o agente de IA (Gemini) |
| Python (em desenvolvimento) | Lógica crítica testável: idempotência, lembretes, regras de negócio |
| Postgres / Redis | Persistência e cache |

**Por que híbrido:** n8n acelera a integração e o agente; Python concentra o que
precisa de testes automatizados e controle de estado.

## Requisitos

- Docker Desktop (com Docker Compose v2)
- Uma conta Google (Google Cloud para a Calendar API)
- Uma chave do Gemini (grátis em https://aistudio.google.com/apikey)
- Um número de WhatsApp para conectar (de preferência um chip de teste)

## Configuração

### 1. Variáveis de ambiente

```Terminal
cp .env.example .env        # Windows: copy .env.example .env
```

Edite o `.env`:

| Variável | O que colocar |
|---|---|
| `AUTHENTICATION_API_KEY` | Chave inventada por você (protege a API da Evolution) |
| `EVOLUTION_DB_PASSWORD` | Senha do Postgres da Evolution (só letras e números) |
| `N8N_DB_PASSWORD` | Senha do Postgres do n8n (só letras e números) |
| `N8N_ENCRYPTION_KEY` | Chave aleatória longa. **Não troque depois de usar.** |

Gerar a chave de criptografia:

```bash
openssl rand -hex 32
```

PowerShell:

```powershell
-join ((1..32) | ForEach-Object { '{0:x2}' -f (Get-Random -Maximum 256) })
```

> O `.env` está no `.gitignore` e **nunca** deve ser commitado.

### 2. Subir os serviços

```bash
docker compose up -d
docker compose ps
```

- Evolution Manager: http://localhost:8080/manager (use a `AUTHENTICATION_API_KEY`)
- n8n: http://localhost:5678 (crie o usuário dono no primeiro acesso)

### 3. Conectar o WhatsApp

```bash
curl -X POST http://localhost:8080/instance/create \
  -H "apikey: SUA_AUTHENTICATION_API_KEY" -H "Content-Type: application/json" \
  -d '{"instanceName":"Agent-Calendar","integration":"WHATSAPP-BAILEYS","qrcode":true,"groupsIgnore":true,"syncFullHistory":false}'
```

Abra o Manager, clique em **Get QR Code** e escaneie em
WhatsApp → Aparelhos conectados. Aguarde o estado `open`:


```bash
curl http://localhost:8080/instance/connectionState/Agent-Calendar -H "apikey: SUA_AUTHENTICATION_API_KEY"
```

### 4. Configurar o n8n

1. **Import from File** e escolha os arquivos de `n8n/workflows/`.
2. Crie as credenciais (elas ficam no n8n, criptografadas, e **não** vão para o Git):
   - **Google Gemini (PaLM) API**: chave do AI Studio.
   - **Google Calendar OAuth2**: no Google Cloud, ative a *Google Calendar API*,
     crie um *OAuth Client ID* (Web application) e cadastre a URI de redirecionamento
     `http://localhost:5678/rest/oauth2-credential/callback`. Cole Client ID/Secret
     no n8n e clique em *Sign in with Google*.
3. **Publique** o workflow.

### 5. Apontar o webhook da Evolution para o n8n

```bash
curl -X POST http://localhost:8080/webhook/set/Agent-Calendar\
  -H "apikey: SUA_AUTHENTICATION_API_KEY" -H "Content-Type: application/json" \
  -d '{"webhook":{"enabled":true,"url":"http://n8n:5678/webhook/agenteIA","byEvents":false,"base64":false,"events":["MESSAGES_UPSERT"]}}'
```

Os containers estão na mesma rede (`evolution-net`), então use o nome `n8n`, não `localhost`.
No n8n, o envio de respostas usa `http://evolution_api:8080/message/sendText/Agent-Calendar`.

### 6. Testar

Envie uma mensagem de **outro número** para o WhatsApp conectado e confira a aba
**Executions** do n8n.

## Estrutura do repositório

```
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── n8n/workflows/      # workflows exportados (sem credenciais)
├── service/            # serviço Python (em desenvolvimento)
└── secrets/            # NÃO versionado
```

Exportar workflows para o Git:

```bash
docker exec n8n n8n export:workflow --all --separate --output=/tmp/workflows
docker cp n8n:/tmp/workflows ./n8n/workflows
```

Antes de commitar, procure nos JSON por chaves, tokens e números de telefone reais.

## Segurança

- Nenhum segredo no repositório: `.env`, `secrets/` e `credentials*.json` estão ignorados.
- Se um segredo for commitado, **troque a chave**; apagar o arquivo depois não basta.
- Credenciais de Google e Gemini ficam no cofre do n8n.
- Use permissões mínimas no Google (apenas Calendar).

## Problemas comuns

| Sintoma | Causa provável |
|---|---|
| `ECONNREFUSED` no log da Evolution | URL do webhook com `localhost`; use `http://n8n:5678/...` |
| `404` no webhook | Workflow não publicado, ou path/método diferente do nó Webhook |
| Erro de senha no Postgres após trocar `.env` | A senha só vale na primeira criação do volume. Use a antiga ou `docker compose down -v` (apaga dados) |
| Credenciais do n8n ilegíveis | `N8N_ENCRYPTION_KEY` foi alterada |
| QR não gera | Versão antiga da Evolution; confira a tag da imagem |

## Limitações conhecidas e melhorias futuras

- Evolution usa o protocolo não oficial (Baileys): há risco de banimento em contas pessoais.
- Serviço Python de lembretes ainda em desenvolvimento.
