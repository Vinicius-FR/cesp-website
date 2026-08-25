# Patch 04 — o site passa a ler do banco

Conserta: *cadastrei um produto no painel e ele não apareceu no site.*

**Tem migração de banco.** É a primeira até agora.

---

## Por que não aparecia

Não era bug. Era a peça que faltava.

```text
painel  ──escreve──▶  D1
                              (não havia fio aqui)
site    ──lê──────▶  catalogo.json
```

O painel sempre gravou no banco. O site sempre leu o arquivo estático. Nada
ligava os dois — esse fio é o `GET /api/catalog`, a primeira rota da camada de
loja. Este patch a implementa e faz o site consumi-la.

Depois dele:

```text
painel  ──escreve──▶  D1  ──/api/catalog──▶  site
                      catalogo.json = rede de segurança
```

Se a API cair, o site volta sozinho para o `catalogo.json` e continua de pé com a
última versão publicada, em vez de mostrar loja vazia. Abra o console do
navegador: ele registra de onde o catálogo veio.

---

## Aplicar

### 1. Migração

Dois campos que o banco não tinha e o site precisa: descrição em inglês e ficha
técnica.

```bash
cd cesp-backend/worker
wrangler d1 execute cesp-orders --remote --file=./migrations/002_catalogo_publico.sql
```

Confira:

```bash
wrangler d1 execute cesp-orders --remote \
  --command "SELECT name FROM pragma_table_info('products') WHERE name IN ('description_en','spec_json')"
```

Tem que listar os dois.

> A ficha é JSON e não tabela: cada produto tem chaves diferentes — carta tem
> `edição` e `estado`, miniatura tem `escala` e `ano`. Coluna fixa não serve.

### 2. Backend

```bash
# substitua src/index.js, schema.sql, wrangler.jsonc, package.json
# e copie testes/catalogo.test.mjs
npm test          # 41 + contrato + 12 + 16
```

No `wrangler.jsonc`, preencha a variável nova:

```jsonc
"API_PUBLIC_BASE": "https://cesp-api.cesp.workers.dev",
```

É com ela que o catálogo monta a URL das fotos guardadas no R2. Sem ela as
imagens vêm com caminho relativo e não carregam no site.

```bash
wrangler deploy
```

Teste antes de mexer no site:

```bash
curl -s https://cesp-api.cesp.workers.dev/api/catalog | python3 -m json.tool | head -40
```

O seu token tem que aparecer aí. Se aparecer aqui e não no site, o problema é o
site; se não aparecer nem aqui, é cadastro (produto inativo?).

### 3. Site

```bash
cd cesp-site
# substitua index.html e admin.html
git add index.html admin.html && git commit -m "site lê do catálogo da API" && git push
```

Nada mais muda: o `API_BASE` do `config.js` já está preenchido.

---

## Depois de aplicar

Volte no painel e complete o produto que você já cadastrou:

- **Descrição (EN)** — vazio faz o site em inglês repetir o português.
- **Ficha técnica** — linhas de chave e valor. Para o seu token:

  | chave | valor PT | valor EN |
  |---|---|---|
  | `formato` | 63 × 88 mm | |
  | `papel` | 300 g | |
  | `corte` | manual | by hand |
  | `verso` | próprio | custom |

  Chave em minúscula e sem acento. As conhecidas (`formato`, `papel`, `ano`,
  `escala`, `estado`, `edicao`, `tiragem`…) já saem traduzidas no site em inglês;
  chave desconhecida aparece como você escreveu.

- **Foto** — enviando pelo painel, ela vai para o R2 e o site monta a URL
  sozinho. O quadro "FOTO" some.

---

## O que mais entrou junto

**Reserva de estoque, funcionando.** O catálogo desconta pedidos pendentes dos
últimos 30 minutos do estoque disponível. Se alguém está no meio do pagamento, o
item não aparece disponível para outra pessoa; se abandonar, volta sozinho. Sem
cron e sem tabela nova.

**Variações no site.** Produto com variações mostra um seletor de tipo na página
do item, com preço e estoque próprios, e a escolha viaja até o carrinho e a
mensagem do WhatsApp. Você não está usando — está criando um produto por arte,
o que também funciona — mas se um dia quiser "Token de Magic" com Soldier,
Zombie e Treasure dentro, já está pronto.

**O catálogo não expõe o que não deve.** Custo de frete, dimensões e valor
declarado ficam no banco e não saem na rota pública. Produto inativo também não
aparece.

---

## Estado depois deste patch

| camada | situação |
|---|---|
| Site, painel, banco, deploy | pronto |
| **Catálogo público** | **pronto** — painel e site ligados |
| Cotação de frete, checkout, webhook, baixa de estoque, etiqueta, e-mail | falta |

O botão de compra continua fechando pelo WhatsApp. O que mudou é que agora o
catálogo é de verdade: cadastrou no painel, apareceu no site.
