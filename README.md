# CESP — configuração, build e deploy

E-commerce serverless: frontend estático no GitHub Pages, backend em Cloudflare
Workers, catálogo e pedidos no D1, imagens no R2, pagamento pela InfinitePay,
frete e etiqueta pelo Melhor Envio, notificação por SMTP.

**Custo: só o domínio.** Todo o resto cabe nos planos gratuitos.

> ## Estado do projeto, sem rodeio
>
> | camada | situação |
> |---|---|
> | Site (vitrine, carrinho, notas, apoio, 2 idiomas) | **pronta** |
> | Painel admin + API de administração | **pronta**, com 33 testes |
> | Banco, bindings, secrets, deploy | **pronto** |
> | **API de loja** — catálogo público, cotação, checkout, webhook, baixa de estoque, etiqueta, e-mail | **NÃO IMPLEMENTADA** |
>
> Na prática: **hoje o site vende pelo WhatsApp**, não por checkout automático.
> Você consegue publicar, cadastrar produto pelo painel e receber pedido — mas o
> pagamento é combinado na conversa. O checkout automático depende da camada de
> loja, detalhada na seção 15.

---

## Índice

1. [Estrutura e os dois repositórios](#1-estrutura-e-os-dois-repositórios)
2. [O que você precisa antes de começar](#2-o-que-você-precisa-antes-de-começar)
3. [Cloudflare: Worker, D1 e R2](#3-cloudflare-worker-d1-e-r2)
4. [Secrets](#4-secrets)
5. [Melhor Envio](#5-melhor-envio)
6. [InfinitePay](#6-infinitepay)
7. [SMTP](#7-smtp)
8. [Deploy do backend](#8-deploy-do-backend)
9. [Deploy do frontend](#9-deploy-do-frontend)
10. [Domínio](#10-domínio)
11. [Cadastrar o primeiro produto](#11-cadastrar-o-primeiro-produto)
12. [Teste ponta a ponta](#12-teste-ponta-a-ponta)
13. [Rotina do dia a dia](#13-rotina-do-dia-a-dia)
14. [O que muda em relação à Silly Cat](#14-o-que-muda-em-relação-à-silly-cat)
15. [Estado atual e o que falta](#15-estado-atual-e-o-que-falta)

---

## 1. Estrutura e os dois repositórios

São **dois repositórios separados**, e isso não é organização — é segurança. O
frontend é público por definição (GitHub Pages serve o repositório inteiro). Se
o Worker morar junto, qualquer pessoa lê o `wrangler.jsonc`, o histórico de
commits e eventualmente um `.dev.vars` que escapou.

```text
cesp-site/                 PÚBLICO — vai para o GitHub Pages
├── index.html             o site inteiro (HTML + CSS + JS)
├── config.js              endereço da API, WhatsApp, redes, apoio
├── catalogo.json          semente do catálogo e fallback se a API cair
├── notas.json             os textos
├── assets/                fotos, favicon, imagem de compartilhamento
└── posts/                 artes do Instagram e as legendas

cesp-backend/              PRIVADO — nunca vai para o Pages
└── worker/
    ├── src/index.js       a API
    ├── migrations/        SQL versionado
    │   └── 001_schema.sql
    ├── schema.sql         cópia do 001, para aplicar de uma vez
    ├── wrangler.jsonc     bindings e configuração não sensível
    ├── package.json
    ├── .dev.vars.example  modelo dos secrets
    └── .gitignore         bloqueia .dev.vars e .env
```

> Confira antes do primeiro `git push` do backend: `git status` não pode listar
> `.dev.vars`. Se listar, o `.gitignore` não está sendo respeitado — provavelmente
> o arquivo foi adicionado antes de existir a regra. Resolve com
> `git rm --cached .dev.vars`.

---

## 2. O que você precisa antes de começar

| item | onde | custo |
|---|---|---|
| Conta Cloudflare | dash.cloudflare.com | grátis |
| Node.js 18+ | nodejs.org | grátis |
| Conta GitHub | github.com | grátis |
| Conta Melhor Envio | melhorenvio.com.br | grátis, paga por etiqueta |
| Conta InfinitePay | infinitepay.io | grátis, taxa por venda |
| Gmail com verificação em duas etapas | para o SMTP | grátis |
| Domínio | onde preferir | ~R$ 40/ano |

```bash
npm install -g wrangler
wrangler login
```

---

## 3. Cloudflare: Worker, D1 e R2

Tudo a partir de `cesp-backend/worker/`.

```bash
cd cesp-backend/worker
npm install
```

**Banco:**

```bash
wrangler d1 create cesp-orders
```

A saída traz um `database_id`. Copie para o `wrangler.jsonc`, no lugar de
`PREENCHER-APOS-d1-create`.

> Nunca reaproveite o `database_id` de outro projeto. O binding do D1 não valida
> dono: ele simplesmente escreve onde você mandar, e você descobre isso quando
> um pedido da CESP aparecer no banco da outra loja.

**Aplicar o esquema:**

```bash
# local, para testar
wrangler d1 execute cesp-orders --local --file=./schema.sql

# produção
wrangler d1 execute cesp-orders --remote --file=./schema.sql
```

**Imagens:**

```bash
wrangler r2 bucket create cesp-product-images
```

O nome já está no `wrangler.jsonc` como `cesp-product-images`. Se você mudar,
mude nos dois lugares.

---

## 4. Secrets

Nada sensível entra no `wrangler.jsonc` — ele vai para o Git. Em produção, cada
valor entra por comando:

```bash
wrangler secret put INFINITEPAY_HANDLE
wrangler secret put MELHOR_ENVIO_TOKEN
wrangler secret put MELHOR_ENVIO_FROM_POSTAL_CODE
wrangler secret put MELHOR_ENVIO_USER_AGENT
wrangler secret put MELHOR_ENVIO_SENDER_JSON
wrangler secret put ADMIN_API_KEY
wrangler secret put SMTP_USER
wrangler secret put SMTP_PASSWORD
wrangler secret put SMTP_FROM
wrangler secret put SALE_NOTIFICATION_TO
```

Para rodar local, copie `.dev.vars.example` para `.dev.vars` e preencha. Esse
arquivo está no `.gitignore` e precisa continuar lá.

O `ADMIN_API_KEY` é a senha do painel. Gere uma de verdade:

```bash
openssl rand -base64 32
```

---

## 5. Melhor Envio

1. Crie a aplicação em **Painel → Integrações → Tokens**.
2. Gere um token com os escopos de **cotação**, **compra de etiqueta** e
   **geração de etiqueta**.
3. O token vai em `MELHOR_ENVIO_TOKEN`, com o prefixo `Bearer `.
4. `MELHOR_ENVIO_SENDER_JSON` é o remetente completo — nome, documento, telefone
   e endereço. É o que sai impresso na etiqueta.
5. `MELHOR_ENVIO_FROM_POSTAL_CODE` é o CEP de origem da cotação.

No `wrangler.jsonc`:

```jsonc
"MELHOR_ENVIO_ENV": "production",       // "sandbox" enquanto testa
"MELHOR_ENVIO_ALLOWED_CARRIERS": "Correios,Jadlog",
"MELHOR_ENVIO_AUTO_LABEL": "true"
```

> **Diferente da Silly Cat:** a CESP usa `declared_value_cents` por produto. Um
> token de R$ 5 não precisa de seguro; uma carta de três dígitos precisa. O
> campo está no esquema desde o começo justamente para você não descobrir isso
> no primeiro extravio.

Teste a cotação antes de vender:

```bash
curl -s "https://cesp-api.SEU-SUBDOMINIO.workers.dev/api/shipping/quote" \
  -H "content-type: application/json" \
  -d '{"postal_code":"01001000","items":[{"id":"token-mtg","quantity":1}]}'
```

---

## 6. InfinitePay

1. Pegue o seu **handle** (o `$seu-nome` do link de pagamento).
2. Coloque em `INFINITEPAY_HANDLE`, **sem o cifrão**.
3. No painel da InfinitePay, cadastre a URL de webhook:

```text
https://cesp-api.SEU-SUBDOMINIO.workers.dev/api/infinitepay/webhook
```

4. A URL de retorno é montada pelo Worker a partir de `STORE_URL`.

> O handle define **para onde vai o dinheiro**. Se você copiar o de outro
> projeto, a venda cai na conta errada e não existe erro na tela avisando.

Webhook e `payment_check` são redundantes de propósito: se o webhook falhar, o
retorno do cliente confirma o pagamento do mesmo jeito, e o sistema não baixa o
estoque duas vezes.

---

## 7. SMTP

Com Gmail:

1. Ative a verificação em duas etapas na conta.
2. Gere uma **senha de app** de 16 dígitos.
3. `SMTP_USER` é o e-mail, `SMTP_PASSWORD` é a senha de app — não a senha da
   conta.
4. `SALE_NOTIFICATION_TO` é onde você quer receber o aviso de venda.

No `wrangler.jsonc`: `smtp.gmail.com`, porta `465`, segurança `implicit`.

---

## 8. Deploy do backend

```bash
cd cesp-backend/worker
wrangler deploy
```

Sai uma URL do tipo `https://cesp-api.SEU-SUBDOMINIO.workers.dev`.

O `src/index.js` que vem no zip **ainda não é a API** — é um Worker mínimo que
existe para você validar a infraestrutura antes de existir lógica de loja:

```bash
curl -s https://cesp-api.SEU-SUBDOMINIO.workers.dev/api/health | python3 -m json.tool
```

A resposta diz se o D1 está ligado, se o esquema foi aplicado, se o R2 responde
e **quais secrets ainda faltam** (só se existem — nunca devolve valor). Enquanto
faltar algo ele responde `503`, então serve de conferência objetiva dos passos
3 a 7. As rotas de loja respondem `501` com explicação, em vez de 404 mudo.

Confira que subiu:

```bash
curl -s https://cesp-api.SEU-SUBDOMINIO.workers.dev/api/catalog | head -c 300
wrangler tail    # log ao vivo, útil no primeiro teste de compra
```

Quando alterar o esquema, crie uma migração nova em `migrations/` em vez de
editar o `001`, aplique e só então faça deploy:

```bash
wrangler d1 execute cesp-orders --remote --file=./migrations/002_algo.sql
wrangler deploy
```

---

## 9. Deploy do frontend

Em `cesp-site/config.js`:

```js
API_BASE: "https://cesp-api.SEU-SUBDOMINIO.workers.dev"
WHATSAPP: "5516999999999"
INSTAGRAM: "https://instagram.com/seu_perfil"
EMAIL: "contato@seudominio"
SITE_URL: "https://seudominio"
```

Com `API_BASE` preenchido, o carrinho vai para o checkout real. Deixando vazio,
ele volta a fechar pedido pelo WhatsApp — útil como plano B se o Worker cair.

```bash
cd cesp-site
git init && git add . && git commit -m "site da CESP"
git branch -M main
git remote add origin git@github.com:SEU-USUARIO/cesp-site.git
git push -u origin main
```

No GitHub: **Settings → Pages → Deploy from a branch → `main` / `/ (root)`**.

Para ver na sua máquina antes:

```bash
python3 -m http.server 8000
```

Abrir o `index.html` com dois cliques não funciona: o navegador bloqueia leitura
de `.json` e chamada de API em `file://`.

**CORS:** o Worker só aceita requisição vinda de `STORE_ORIGIN`. Enquanto testa
em `localhost`, acrescente a origem local nessa variável do `wrangler.jsonc` e
faça deploy de novo — senão o carrinho falha sem mensagem clara.

---

## 10. Domínio

Arquivo `CNAME` na raiz do `cesp-site`, uma linha:

```text
cesp.seudominio.com
```

No DNS, um `CNAME` de `cesp` para `SEU-USUARIO.github.io`. Depois, em
Settings → Pages, marque **Enforce HTTPS**.

Atualize `STORE_ORIGIN` e `STORE_URL` no `wrangler.jsonc` para o domínio final e
faça deploy do Worker de novo.

> Se você já tem outro site no Pages com domínio próprio, não reaproveite o
> arquivo `CNAME` dele. Dois repositórios reivindicando o mesmo domínio derrubam
> a configuração do primeiro.

---

## 11. Cadastrar o primeiro produto

O `catalogo.json` é **semente e fallback**, não a fonte da verdade. Quem manda é
o D1. No primeiro deploy o Worker semeia o banco a partir dele; depois disso,
cadastro e estoque passam a ser pelo painel.

### Modelo de produto

| campo | o que é |
|---|---|
| `id` | único, sem espaço. Vira o endereço: `#/item/token-mtg` |
| `cat` | `cards` `cars` `comics` `blocks` `games` `apps` |
| `ativo` | `false` esconde do site — use para rascunho |
| `preco` | **em centavos**. `500` = R$ 5,00. `0` = acervo, não está à venda |
| `estoque` | unidades prontas (ou soma das variações) |
| `repro` | `true` = você produz mais; `false` = peça única |
| `producao_dias` | prazo quando o estoque zera e o item é reproduzível |
| `declared_value_cents` | valor declarado no frete. Deixe 0 para itens baratos |
| `fotos` | `["assets/nome.jpg"]`. A primeira é a capa |
| `peso_kg`, `caixa_cm` | **obrigatórios para cotar frete** |
| `variacoes` | opcional — veja abaixo |

### Variações

Variação é o que resolve o seu caso dos tokens. "8 em estoque" não são 8
unidades iguais: são tipos diferentes, e o comprador escolhe qual quer.

```json
{
  "id": "token-mtg",
  "nome": "Token de Magic",
  "preco": 500,
  "variacoes": [
    { "id": "soldier",  "nome": "Soldier 1/1",  "estoque": 3 },
    { "id": "zombie",   "nome": "Zombie 2/2",   "estoque": 2 },
    { "id": "treasure", "nome": "Treasure",     "estoque": 3, "preco": 600 }
  ]
}
```

Regras: estoque é **por variação**; `preco` na variação sobrescreve o do produto,
e ausente herda; a variação escolhida acompanha o item até o carrinho, o pedido,
o e-mail e a baixa de estoque.

### Fotos

Vão em `assets/`, cerca de 1600 px no lado maior, JPG. Pelo painel, a imagem
sobe para o R2 e é servida por `/api/product-images/`.

---

## 12. Teste ponta a ponta

Faça isso **antes de divulgar**, com um produto de R$ 1,00 e estoque 1:

1. Abra o site e confirme que o produto aparece.
2. Adicione ao carrinho e escolha uma variação, se houver.
3. Informe um CEP e confira se a cotação volta com prazo.
4. Vá até o pagamento e pague de verdade.
5. Confirme que o pedido apareceu no painel com status `paid`.
6. Confirme que o e-mail de venda chegou.
7. Confirme que **o estoque baixou de 1 para 0** e o produto sumiu da vitrine.
8. Confira a etiqueta gerada no Melhor Envio.
9. Arquive o produto de teste — não apague.

```bash
wrangler tail    # deixe rodando durante o teste
```

Se algum passo falhar, o log ao vivo mostra em qual. Testar com produto barato
é mais rápido que ler código.

---

## 13. Rotina do dia a dia

| tarefa | onde |
|---|---|
| Produto novo, foto, preço, estoque | painel admin |
| Ajustar estoque | painel admin (fica registrado como ajuste) |
| Tirar produto de circulação | **arquivar**, nunca apagar — pedido antigo aponta para ele |
| Texto novo | `notas.json`, commit |
| Mudar preço | painel admin |
| Post do Instagram | `folha/post.py` e `folha/folha.py` |

Produto **arquivado** sai da vitrine mas continua existindo para os pedidos que o
referenciam. Apagar quebra o histórico.

---

## 14. O que muda em relação à Silly Cat

A arquitetura é a mesma. Três coisas mudam por causa do catálogo, e é importante
entender por quê:

**1. Item não reproduzível bloqueia.** Na Silly Cat, estoque zero vira encomenda:
vende e crocheta outro. Na CESP isso vale para token e baralho que você imprime
(`repro: true`), mas **não** para peça de acervo. Uma carta de 1993 não sai da
impressora em 7 dias. Por isso existe o campo, e por isso item com `repro: false`
e estoque zero mostra "esgotado" em vez de oferecer produção.

**2. Reserva no checkout.** A Silly Cat baixa estoque só depois do pagamento
confirmado, e para crochê isso basta. Na CESP a maioria dos itens tem estoque 1,
então dois compradores podem pagar o mesmo item no mesmo minuto — e o prejuízo é
estornar alguém que já pagou. A solução não pede serviço novo: o pedido pendente
já é a reserva, e some da conta por idade.

```sql
disponivel = estoque - (
  SELECT COALESCE(SUM(oi.quantity), 0)
  FROM order_items oi JOIN orders o ON o.order_nsu = oi.order_nsu
  WHERE oi.product_id = ? AND o.status = 'pending'
    AND o.created_at > datetime('now', '-30 minutes')
)
```

Sem cron, sem tabela nova, sem custo. Expira por deixar de ser contado.

**3. Valor declarado.** Campo `declared_value_cents` por produto, para o seguro
do frete em item caro.

---

## 15. Estado atual e o que falta

**Pronto:**

- Frontend completo: catálogo, categorias, carrinho, item, notas, apoio, dois idiomas
- **Painel administrativo** (`admin.html`) e a camada admin do Worker: login com
  sessão, produtos, variações, estoque com histórico, imagens no R2 e pedidos.
  Coberto por 33 testes automatizados contra banco real (`worker/testes/`)
- `schema.sql` com produtos, variações, imagens, estoque, pedidos, etiquetas, admin
- `wrangler.jsonc` com bindings e a lista de secrets
- Ferramentas de post do Instagram

**Falta, e é o próximo passo:**

- **A camada de loja do Worker**: `/api/catalog`, cotação de frete, checkout,
  webhook da InfinitePay, `payment_check`, baixa de estoque, etiqueta e SMTP.
- Ligar o frontend na API: hoje ele lê `catalogo.json` direto e o botão de
  pagamento cai no WhatsApp quando `API_BASE` está vazio.

Enquanto o Worker não sobe, o site funciona e vende pelo WhatsApp. Não é o
destino, mas é melhor que perfil sem site — e a troca depois é uma linha no
`config.js`.


---

## 16. Segurança: o que é público e o que não é

**A URL da API é pública, e isso não é falha.** O navegador do cliente precisa
chamá-la para montar a vitrine e fechar pedido; ela aparece no DevTools de
qualquer visitante. O mesmo vale para o `config.js` e para o `admin.html`, que
ficam no repositório público do site.

O que protege não é esconder a URL — é cada rota decidir quem pode chamá-la:

| rota | quem pode |
|---|---|
| `/api/catalog`, `/api/shipping/quote`, `/api/checkout` | qualquer um. É a loja |
| `/api/product-images/*` | qualquer um. São as fotos dos produtos |
| `/api/infinitepay/webhook` | a InfinitePay, validado pelo conteúdo |
| **`/api/admin/*`** | **só com sessão válida** |

**Por que `config.js` não vira secret:** não existe segredo em código de
frontend. Qualquer valor que o navegador precise ler, o visitante também lê —
minificar ou ofuscar só atrasa. Por isso o `config.js` só tem coisa pública:
endereço da API, WhatsApp, Instagram, chave Pix. Nenhum desses abre porta.

O que **nunca** pode ir para lá: `ADMIN_API_KEY`, token do Melhor Envio, senha
de SMTP. Esses vivem só como secret do Worker.

**Como o painel se autentica:**

1. Você digita a chave. Ela vai uma vez para `/api/admin/login`.
2. O Worker compara em tempo constante e devolve um **token de sessão** de 8 h.
3. O banco guarda o **hash** do token, não o token — vazamento de banco não vira
   sessão.
4. O token fica em `sessionStorage`: morre quando você fecha a aba.
5. Oito tentativas erradas em 15 minutos bloqueiam o IP.

**A chave nunca é gravada em disco em lugar nenhum.** Nem no repositório, nem no
navegador.

Três recomendações que não estão no código:

- Gere a chave com `openssl rand -base64 32`. Chave curta derruba tudo isso.
- Troque a chave se suspeitar de qualquer coisa: `wrangler secret put ADMIN_API_KEY`
  invalida logins futuros na hora.
- O `admin.html` é público como arquivo, e está com `noindex`. Isso evita
  buscador, não evita quem tenta o endereço — e não precisa evitar, porque sem
  a chave a página é um formulário que não faz nada.
