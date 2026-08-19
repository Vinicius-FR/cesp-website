# Os quatro primeiros posts

Imagens em `posts/`. Texto na imagem é curto e todo em inglês; a legenda vai
em português primeiro e inglês depois, separados por um travessão sozinho.

Os três primeiros estão como **template**: o quadro da foto está vazio, com o
marcador `PHOTO`. Fotografe, rode o mesmo comando passando o arquivo, e ele
substitui. Nada mais muda.

---

## 01 · Apresentação

```bash
python3 post.py capa --cat U,R,G --caminho "~" --cmd "whoami" \
  --frase "Collect. Resell. Build the tools." \
  --selo "collector's edition" --saida ../posts/01-apresentacao.png
```

**Legenda:**

```
Isto aqui é a CESP — Collector's Edition Softwares & Products.

Coleciono algumas peças, revendo outras, e no tempo livre desenvolvo software.

Seis pastas: cards, cars, comics, blocks, games e apps. Boa parte é acervo e não
está à venda. O que está, está com preço.

Começo com os tokens de Magic e Yu-Gi-Oh, impressos e cortados aqui, e com o
compositor de cartas que escrevi para fazer eles. A ferramenta é grátis e vai
continuar sendo.

Site no link da bio.

—

This is CESP — Collector's Edition Softwares & Products.

I collect some pieces, resell others, and build software in my free time.

Six folders: cards, cars, comics, blocks, games and apps. Most of it is my own
collection and not for sale. Whatever is, carries a price.

Starting with Magic and Yu-Gi-Oh tokens, printed and cut here, and the card
composer I wrote to make them. The tool is free and will stay free.

Site in bio.
```

---

## 02 · Tokens de Magic

```bash
python3 post.py foto SUA-FOTO.jpg --cat G --caminho "~/games" \
  --cmd "open magic-token.jpg" --titulo "Magic Tokens" \
  --meta "63 × 88 mm · 300 g · custom back · 8 in stock" \
  --preco "R$ 5,00" --saida ../posts/02-magic.png
```

**Legenda:**

```
Token de Magic · R$ 5 cada.

Impresso e cortado aqui, papel 300 g, tamanho padrão de carta (63 × 88 mm),
verso próprio. Arte única por token nesta primeira leva — você escolhe o tipo
no pedido.

8 unidades prontas. Se acabar, faço mais em cerca de 5 dias.

Pedido pelo site (link na bio) ou aqui no direct.
Fora do Brasil: me chama no direct que a gente resolve o envio.

—

Magic tokens · R$ 5 each.

Printed and cut here on 300 g stock, standard card size (63 × 88 mm), custom
back. One artwork per token in this first run — you pick the type when ordering.

8 units ready. If they run out, I make more in about 5 days.

Order through the site (link in bio) or right here in the DMs.
Outside Brazil: DM me and we'll sort out shipping.
```

---

## 03 · Tokens de Yu-Gi-Oh

```bash
python3 post.py foto SUA-FOTO.jpg --cat G --caminho "~/games" \
  --cmd "open yugioh-token.jpg" --titulo "Yu-Gi-Oh Tokens" \
  --meta "59 × 86 mm · 300 g · custom back · 6 in stock" \
  --preco "R$ 4,00" --saida ../posts/03-yugioh.png
```

**Legenda:**

```
Token de Yu-Gi-Oh · R$ 4 cada.

Mesmo processo dos de Magic: papel 300 g, corte manual, verso próprio. Aqui no
tamanho padrão de Yu-Gi-Oh, 59 × 86 mm. Arte única por token nesta primeira leva.

6 unidades prontas. Acabando, faço mais em cerca de 5 dias.

Pedido pelo site (link na bio) ou aqui no direct.
Fora do Brasil: me chama no direct.

—

Yu-Gi-Oh tokens · R$ 4 each.

Same process as the Magic ones: 300 g stock, cut by hand, custom back. This one
in standard Yu-Gi-Oh size, 59 × 86 mm. One artwork per token in this first run.

6 units ready. When they run out, I make more in about 5 days.

Order through the site (link in bio) or right here in the DMs.
Outside Brazil: just DM me.
```

---

## 04 · A coleção

```bash
python3 folha.py SUAS-FOTOS/ --layout 3x3 --cat R --caminho "~/cars" \
  --cmd "montage *.jpg -tile 3x3" --titulo "From the shelf" \
  --meta "Hot Wheels · not for sale" --selo "collection" \
  --saida ../posts/04-colecao.png
```

**Legenda:**

```
Uma parte da prateleira.

Nada aqui está à venda — isso é acervo, e acervo fica. Coloquei no site na pasta
cars/ com ficha de cada um: série, ano, escala e estado.

A numeração nas fotos serve para conversa: se você quiser saber de um específico,
é só falar o número.

Aos poucos vou subindo o resto — cartas, quadrinhos e Lego têm cada um a sua
pasta esperando.

—

Part of the shelf.

None of this is for sale — it's the collection, and the collection stays. It's
on the site under cars/ with a spec sheet for each: series, year, scale and
condition.

The numbers on the photos are there for conversation: if you want to know about
a specific one, just say the number.

The rest goes up little by little — cards, comics and Lego each have a folder
waiting.
```

---

## Ordem de publicação

01 primeiro e fixado no perfil. Depois 02 e 04 com um dia de intervalo, e 03 no
dia seguinte. Assim o perfil não abre com duas vendas seguidas.

## Hashtag

Cinco a oito, no primeiro comentário e não na legenda. Específicas funcionam
melhor que genéricas: `#magictokens` `#mtgtokens` `#yugiohtokens` `#tokenaltered`
`#hotwheelscollector` valem mais que `#colecionador`.
