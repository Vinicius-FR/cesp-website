# Patch 03 — "chave incorreta" e como resolver

**Não tem migração de banco.** Só código.

---

## Primeiro: você não consegue ler o secret

`wrangler secret list` mostra **só os nomes**, nunca os valores. A Cloudflare não
devolve o conteúdo de um secret nem para o dono da conta — é assim de propósito,
e é o motivo de ele ser seguro.

Então não existe "descobrir qual senha foi salva". Existe **regravar**.

---

## Antes de regravar, a causa provável

O jeito mais comum de gravar um secret errado sem perceber é levar junto um
espaço ou uma quebra de linha. Testei os quatro casos com o código antigo:

| como a chave foi gravada | login |
|---|---|
| exata | aceita |
| com `\n` no fim | **rejeitava** |
| com espaço no fim | **rejeitava** |
| colada do Windows, com `\r\n` | **rejeitava** |

Isso acontece quando você faz `echo "chave" \| wrangler secret put`, quando cola
selecionando a linha inteira do terminal, ou quando o editor acrescenta quebra de
linha ao salvar. Você digita a chave certa no painel e ela é rejeitada, porque o
que está guardado tem um caractere invisível a mais.

**Este patch corrige isso:** a comparação passou a ignorar espaço e quebra de
linha nas duas pontas. Se era esse o seu caso, o login volta a funcionar com a
chave que você anotou, sem precisar trocar nada.

---

## Aplicar

```bash
cd cesp-backend/worker
# substitua src/index.js e testes/admin.test.mjs
npm test          # espere 40 passaram + contrato completo + 12 passaram
wrangler deploy
```

Depois tente entrar de novo com a chave que você anotou.

---

## Se ainda não entrar

### 1. Veja se o Worker acusa lixo na chave

```bash
curl -s https://cesp-api.cesp.workers.dev/api/health | python3 -m json.tool | grep -A3 avisos
```

Se aparecer *"ADMIN_API_KEY foi gravada com espaço ou quebra de linha nas
pontas"*, era isso. O login já funciona, mas regrave limpo mesmo assim.

O aviso não revela nada da chave — só diz que ela tem lixo nas bordas.

### 2. Você pode estar bloqueado, não errado

Oito tentativas erradas em 15 minutos bloqueiam o seu IP, e depois disso **nem a
chave certa passa**. A resposta nesse caso é `429`, mas dá para confundir com
senha errada se você não olhou o código.

Limpe o bloqueio direto no banco:

```bash
wrangler d1 execute cesp-orders --remote \
  --command "DELETE FROM app_meta WHERE key LIKE 'login_fail:%'"
```

### 3. Regrave a chave

```bash
openssl rand -base64 32 | tr -d '\n' | pbcopy      # macOS
openssl rand -base64 32 | tr -d '\n' | clip        # Windows
openssl rand -base64 32 | tr -d '\n'               # e copie da tela
```

O `tr -d '\n'` é o detalhe que evita o problema todo.

```bash
wrangler secret put ADMIN_API_KEY
# cole a chave quando ele pedir, e dê Enter uma vez só
```

Guarde no gerenciador de senhas **antes** de fechar o terminal. Não vai dar para
consultar depois.

Secret entra em vigor na hora, **sem precisar de `wrangler deploy`**.

### 4. Teste por fora do navegador

Isolar o navegador tira CORS, cache e digitação da equação:

```bash
curl -s -X POST https://cesp-api.cesp.workers.dev/api/admin/login \
  -H "content-type: application/json" \
  -d '{"key":"SUA-CHAVE-AQUI"}'
```

- Voltou `{"token":"..."}` → a chave está certa, o problema é o navegador.
  Recarregue o painel com Ctrl+Shift+R.
- Voltou `chave incorreta (n/8)` → é a chave mesmo. Volte ao passo 3.
- Voltou `bloqueado` → passo 2.
- Voltou `ADMIN_API_KEY não configurada` → o secret não existe nesse Worker.
  Confira se você não gravou em outro nome ou em outro ambiente:
  `wrangler secret list`.

---

## Uma observação sobre a chave

Se a sua chave é curta ou memorizável, troque por uma de 32 bytes aleatórios
mesmo agora que o login funciona. O limite de tentativas segura ataque de força
bruta, mas ele existe para dar tempo — não para substituir uma chave boa.
