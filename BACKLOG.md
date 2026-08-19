# O que adicionar depois

Anotado enquanto o site era montado. A ordem é por retorno sobre esforço, não
por gosto.

---

## Antes de vender pra valer

- **Backend.** Worker + D1 + R2 no Cloudflare, com o `schema.sql` e o
  `wrangler.jsonc` que já estão prontos na pasta `backend/`. Falta portar o
  `index.js`, adaptando duas coisas do projeto de origem: bloquear item com
  `reproducible = 0` quando o estoque zera, e descontar pedidos pendentes na
  hora de calcular disponibilidade. A consulta da reserva já foi escrita e
  testada — não precisa de cron nem de serviço novo.
- **Valor declarado no frete.** O campo `declared_value_cents` está no esquema
  mas ainda não é usado. Enquanto só houver token de R$ 35 isso não importa; no
  dia que entrar uma carta de três dígitos, importa muito.
- **Páginas de entrega e devolução.** O rodapé já prevê os links. Vender sem
  eles funciona, mas gera pergunta repetida no direct.
- **Prazo de produção visível antes do carrinho.** Hoje o "+5 dias" só aparece
  na página do item.

## Conteúdo, na ordem que você já disse

- Hot Wheels: preencher os três rascunhos e ir somando o resto da coleção.
- `cards/`: Magic, Yu-Gi-Oh e Card Wars do acervo.
- `comics/`: Hora de Aventura.
- `blocks/`: Lego.
- Card Wars Classic como software público em `apps/` — é o item mais forte que
  você tem para atrair gente, e é grátis.
- Mais artes de token. O catálogo hoje diz "arte única por token"; quando houver
  variantes, o item precisa de escolha de arte no carrinho.

## Site

- **Galeria de item com clique para ampliar.** Hoje a foto é estática.
- **Busca.** Só faz sentido acima de umas 40 peças.
- **Ordenação e filtro** na listagem: preço, mais recente, só disponível.
- **Notas em inglês.** A estrutura já suporta; falta escrever.
- **RSS das notas.** Barato de gerar, e é o que faz alguém acompanhar sem
  depender do Instagram.
- **`sitemap.xml` e `robots.txt`.** Rota com `#` não é indexada bem; se busca
  vier a importar, vale trocar o roteamento por caminho de verdade.
- **Página do compositor dentro do site**, em vez de link para fora.

## Ferramentas

- **`post.py` gravando o registro do item.** A ideia que ficou pendente: quando
  você gera o post do Instagram já digita nome, ficha e preço — esses dados
  deveriam virar uma entrada no `catalogo.json` sozinhos, em vez de você digitar
  duas vezes.
- **`--peso` e `--caixa` nos scripts**, pelo mesmo motivo: sem peso e dimensão o
  Melhor Envio não cota, e capturar isso na hora da foto evita tocar no item
  duas vezes.
- **Gerador de miniatura.** Hoje a foto vai no tamanho que você subir; um passo
  de redimensionamento economiza banda e tempo de carregamento no celular.

## Instagram

- Sétimo destaque `vendidos`, com prova de entrega e embalagem.
- Os nove posts da grade de lançamento.

---

## Decisões já tomadas, para não reabrir sem motivo

- Fonte da Lego não entra: é marca registrada e, na renderização em pontos, muda
  1,9% do desenho. Risco alto, ganho nenhum.
- Verde vivo é o fósforo padrão; P1 e âmbar existem para quando a peça depender
  de ler o verde de mana.
- Branco sobre fundo claro sempre leva filete — tem 1,5:1 de contraste sozinho.
- Caminho, comando e nome de pasta ficam em inglês nos dois idiomas.
- No máximo três cores de mana acesas por post.
