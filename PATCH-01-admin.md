# Patch 01 — Painel administrativo

Para quem **já completou o README principal**: D1 criado, esquema aplicado,
secrets configurados, Worker publicado e site no ar.

**Não tem migração de banco.** O `schema.sql` deste patch é byte a byte igual ao
que você já aplicou — `product_variants`, `product_images` e `app_meta` já
estavam lá. Este patch é só código.

Tempo estimado: 10 minutos.

---

## O que entra

| arquivo | situação |
|---|---|
| `cesp-backend/worker/src/index.js` | **substitui** o anterior |
| `cesp-backend/worker/testes/` | novo — 3 arquivos |
| `cesp-backend/worker/package.json` | ganhou o script `test` |
| `cesp-site/admin.html` | novo |

O Worker anterior só tinha `/api/health`. Este tem a camada administrativa
inteira: login com sessão, produtos, variações, estoque com histórico, imagens
no R2 e pedidos. As rotas de loja continuam respondendo `501`.

---

## 1. Backend

```bash
cd cesp-backend/worker

# substitua src/index.js e package.json, e copie a pasta testes/
npm test
```

Espere ver:

```text
33 passaram, 0 falharam
contrato completo: painel e Worker batem
```

Os testes rodam contra um SQLite em memória com o seu `schema.sql` — não tocam
no banco de produção e não precisam de internet. Se falharem, **não faça deploy**:
o erro está no código, não na sua configuração.

```bash
wrangler deploy
```

---

## 2. Confirme que a camada subiu

```bash
curl -s https://cesp-api.SEU-SUBDOMINIO.workers.dev/api/health | python3 -m json.tool
```

Procure por:

```json
"camadas": { "admin": "pronta", "loja": "nao_implementada" }
```

Se `secrets.ADMIN_API_KEY` estiver `false`, o login não funciona. Resolva agora:

```bash
openssl rand -base64 32          # gere uma chave de verdade
wrangler secret put ADMIN_API_KEY
wrangler deploy
```

---

## 3. Site

Copie `admin.html` para a raiz do `cesp-site` e publique:

```bash
cd cesp-site
git add admin.html
git commit -m "painel administrativo"
git push
```

O painel lê `API_BASE` do `config.js` que já está lá. Se estiver vazio, a página
abre explicando isso em vez de dar erro.

Acesse em `https://seudominio/admin.html`.

---

## 4. Teste de segurança antes de usar

Faça os quatro, nesta ordem. São 2 minutos e valem mais que ler o código:

```bash
API=https://cesp-api.SEU-SUBDOMINIO.workers.dev

# 1. sem token não lista nada -> espere 401
curl -s -o /dev/null -w "%{http_code}\n" $API/api/admin/products

# 2. token inventado -> espere 401
curl -s -o /dev/null -w "%{http_code}\n" -H "authorization: Bearer nada" $API/api/admin/products

# 3. chave errada -> espere 401
curl -s -X POST $API/api/admin/login -H "content-type: application/json" -d '{"key":"errada"}'

# 4. chave certa -> espere um token
curl -s -X POST $API/api/admin/login -H "content-type: application/json" -d '{"key":"SUA-CHAVE"}'
```

O quarto devolve `{"token":"...","expira_em":"..."}`. Esse token vale 8 horas e
**não é** a sua chave — o que o banco guarda é o hash dele.

> Se você errar a chave 8 vezes em 15 minutos, o seu IP é bloqueado e nem a chave
> certa passa. É proposital. Espere os 15 minutos.

---

## 5. Cadastre os tokens com variações

É aqui que o painel resolve o problema que o `catalogo.json` não resolvia: os
8 tokens de Magic não são 8 unidades iguais, são tipos diferentes.

1. Entre no painel e clique **+ produto**.
2. ID `token-mtg`, nome "Token de Magic", preço `5,00`, categoria `games`.
3. Marque **reproduzível** e ponha 5 dias de produção.
4. Frete: 16 × 1 × 12 cm, 0,02 kg.
5. Em **Variações**, adicione uma linha por tipo de token, cada uma com o seu
   estoque. Deixe o preço vazio para herdar os R$ 5,00; preencha só onde for
   diferente.
6. Salve e confira: o estoque total mostrado é a **soma das variações**.

Repita para `token-ygo` com R$ 4,00 e os tipos de Yu-Gi-Oh.

O compositor (`compositor`, categoria `apps`, preço 0) e os Hot Wheels de acervo
(preço 0, **não** reproduzível) entram do mesmo jeito.

### Detalhes que economizam dor depois

- **Preço 0 significa acervo**, não grátis. O item aparece marcado como coleção
  pessoal e sem botão de compra.
- **Reproduzível desmarcado + estoque 0 = esgotado de verdade.** É o que impede
  vender duas vezes uma peça única.
- **Arquivar não é apagar.** Produto arquivado sai da loja mas continua
  existindo para os pedidos que apontam para ele. O botão de apagar, no fundo,
  arquiva.
- **Variação removida vira inativa**, pelo mesmo motivo.
- Toda mudança de estoque fica no **histórico**, inclusive as feitas pelo editor.

---

## 6. Depois de cadastrar

O site ainda lê o `catalogo.json`, não o banco — ligar os dois é a camada de
loja, que ainda não existe. Enquanto isso:

- Use o **Exportar JSON** do painel para gerar o catálogo a partir do banco e
  manter o `catalogo.json` do site em dia. Não é automático ainda.
- Mantenha `API_BASE` preenchido no `config.js`: ele já serve o painel, e o
  botão de compra continua caindo no WhatsApp porque a rota de checkout responde
  `501` — o site trata isso e não quebra.

---

## Se der errado

| sintoma | causa provável |
|---|---|
| Painel abre mas o login não responde | `STORE_ORIGIN` não bate com o domínio do site. Ajuste no `wrangler.jsonc` e faça deploy |
| `503 ADMIN_API_KEY não configurada` | falta `wrangler secret put ADMIN_API_KEY` |
| `401` logo depois de entrar | sessão expirou (8 h) ou você fechou e reabriu a aba |
| `429 muitas tentativas` | 8 erros em 15 minutos. Espere |
| Imagem some depois de enviar | binding R2 ausente. Confira `bindings.R2` no `/api/health` |
| Lista vazia com produtos cadastrados | filtro em "com estoque" e tudo com estoque 0 |

Log ao vivo, para qualquer um deles:

```bash
wrangler tail
```
