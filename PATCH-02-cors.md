# Patch 02 — CORS com mais de uma origem

Conserta o `Failed to fetch` no login do painel.

**Não tem migração de banco.** Só código.

---

## O que acontecia

```text
Access to fetch at 'https://cesp-api.cesp.workers.dev/api/admin/login'
from origin 'https://www.collectorsedition.club' has been blocked by CORS policy:
The 'Access-Control-Allow-Origin' header has a value 'https://collectorsedition.club'
that is not equal to the supplied origin.
```

Para o navegador, `https://collectorsedition.club` e
`https://www.collectorsedition.club` são **origens diferentes**. O Worker estava
respondendo com uma string fixa, então só uma das duas funcionava — e o site
estava servindo pela outra.

O erro aparece no login porque essa é a primeira chamada à API. Não tem nada a
ver com a chave: a requisição nem chegou a ser enviada, o navegador barrou antes.

---

## Aplicar

```bash
cd cesp-backend/worker
# substitua src/index.js e package.json, e copie testes/cors.test.mjs
npm test
```

Espere `33 passaram` + `contrato completo` + `12 passaram`.

Depois, no `wrangler.jsonc`, troque `STORE_ORIGIN` por uma **lista**:

```jsonc
"STORE_ORIGIN": "https://www.collectorsedition.club,https://collectorsedition.club,http://localhost:8000",
"STORE_URL": "https://www.collectorsedition.club",
```

`STORE_URL` continua sendo **uma só** — é para onde o cliente volta depois de
pagar, então tem que ser a canônica, a que você usa de verdade.

```bash
wrangler deploy
```

---

## Conferir

```bash
curl -s https://cesp-api.cesp.workers.dev/api/health | python3 -m json.tool | grep -A6 origens
```

Deve listar as origens aceitas. Agora simule o navegador:

```bash
curl -s -o /dev/null -D - -X OPTIONS \
  https://cesp-api.cesp.workers.dev/api/admin/login \
  -H "origin: https://www.collectorsedition.club" \
  -H "access-control-request-method: POST" | grep -i "access-control-allow-origin"
```

Tem que voltar exatamente a origem que você mandou. Se voltar outra, o
`STORE_ORIGIN` não subiu — confira se fez `wrangler deploy` depois de editar.

Recarregue o painel com **Ctrl+Shift+R**. O navegador guarda o preflight por até
24 horas, e sem isso você pode ver o erro antigo mesmo com o Worker já corrigido.

---

## O que mudou no comportamento

- `STORE_ORIGIN` aceita lista separada por vírgula.
- O Worker devolve **a origem que o navegador pediu**, se ela estiver na lista.
- Também aceita o irmão `www`/apex de cada item listado — continua sendo um
  conjunto fechado, tirado da sua configuração, não um curinga.
- Origem fora da lista recebe a canônica, e o navegador bloqueia. É o
  comportamento correto: não existe "bloquear no servidor" em CORS.
- Passou a mandar `Vary: Origin`, senão um cache intermediário pode servir o
  header de uma origem para outra.
- `/api/health` agora lista `origens_aceitas`, para depurar sem adivinhar.

Barra sobrando na configuração (`https://site.com/`) não quebra mais.

---

## Por que isso passou nos testes anteriores

Os 33 testes usavam sempre a mesma origem, então a diferença entre "string fixa"
e "lista" nunca aparecia. Só quebra quando a origem do navegador difere da
configurada — exatamente o seu caso, e exatamente o tipo de coisa que só o
deploy real revela.

Agora tem `testes/cors.test.mjs` com 12 casos, incluindo o seu erro reproduzido:
site em `www` com apex configurado. Também cobre o lado que importa: origem de
terceiro não é ecoada, e domínio que só *começa* parecido
(`collectorsedition.club.malicioso.com`) não passa.
