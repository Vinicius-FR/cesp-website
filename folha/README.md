# folha.py — colagem CESP a partir de fotos soltas

Monta o post de colagem no template da CESP: linha de comando no topo, grade de
fotos numeradas, título, ficha e barra de mana na borda direita.

Mesma lógica do compositor de tokens: **nenhuma medida é pixel absoluto**. Todo o
chrome é fração da largura do quadro, então `--tam 1080` e `--tam 2160` produzem
exatamente o mesmo desenho, um servindo para o Instagram e outro para arquivo.

## Instalar

```bash
pip install pillow
```

Só isso. As fontes já vêm na pasta `fontes/` (JetBrains Mono e Silkscreen, ambas
sob licença OFL, baixadas do repositório do Google Fonts). Se elas sumirem, o
script cai numa monoespaçada do sistema em vez de quebrar.

## Usar

```bash
python3 folha.py fotos/ \
  --layout 3x3 --cat U,R,G \
  --caminho "~/cars" --cmd "montage *.jpg -tile 3x3" \
  --titulo "Coleção F1 · 1988—1994" \
  --meta "9 miniaturas · 1:43 · o 04 e o 07 estão à venda" \
  --selo acervo --saida post.png
```

Destaque com preço:

```bash
python3 folha.py foto-1.jpg foto-2.jpg foto-3.jpg foto-4.jpg foto-5.jpg \
  --layout hero --cat U --caminho "~/cards" \
  --titulo "Underground Sea" --meta "Revised · 1994 · verso, bordas e centralização" \
  --preco "R$ 4.200,00" --saida venda.png
```

Passo a passo no tema claro:

```bash
python3 folha.py passos/ --layout 3x2 --tema claro --cat G \
  --caminho "~/games" --titulo "Como imprimo um baralho" \
  --meta "do arquivo ao corte · 6 passos" --selo "ateliê"
```

## Opções

| flag | o que faz |
|---|---|
| `--layout` | `3x3` (9 fotos), `3x2` (6), `2x2` (4), `hero` (1 grande + 4) |
| `--cat` | categorias acesas na barra: `W,U,B,R,G,I`. Várias = post multicolorido |
| `--caminho` | o caminho no prompt, ex. `~/cars` |
| `--cmd` | o comando mostrado depois do `$` |
| `--titulo` / `--meta` | título e ficha embaixo da grade |
| `--selo` | texto pequeno à direita no rodapé |
| `--preco` | ex. `"R$ 340,00"` — desenha o bloco vermelho e substitui o selo |
| `--tema` | `escuro` (padrão) ou `claro` |
| `--corte` | `auto` (padrão), `centro`, `topo` |
| `--margem` | folga em volta do assunto no corte automático, padrão `0.20` |
| `--tam` | lado do quadro em px, padrão `1080` |
| `--sem-numero` | tira a numeração das células |
| `--saida` | arquivo de saída |

Se você jogar mais fotos do que cabe no layout, o script gera várias folhas
(`post-01.png`, `post-02.png`, …) e avisa quantas células ficaram vazias.

## Sobre o corte automático

O modo `auto` encontra o objeto na foto e **aproxima** nele. Isso importa mais do
que parece: foto de celular é 4:3, a célula é ~3:2, e só ajustar a proporção
recorta tão pouco que a miniatura continua perdida no meio do feltro.

Medido em dois conjuntos de nove fotos, comparando `auto` contra `centro`:

| | desvio do assunto ao centro | variação de tamanho entre células |
|---|---|---|
| fotos mal enquadradas, corte central | 26,1% | 41% |
| só aproximando no assunto | 5,7% | 2% |
| aproximando + estendendo o fundo | **0,5%** | **2%** |

Medido célula a célula na imagem final, com o objeto espalhado entre 14% e 86%
do quadro nas fotos de origem.

A segunda coluna é a que faz a folha parecer profissional: sem ela, um item sai
gigante e o vizinho sai minúsculo, e a grade vira bagunça.

### Estender o fundo

Quando o item está perto da beirada da foto, a janela de corte esbarra no limite
da imagem e trava ali — o item sai torto e não tem como centralizar. Se o fundo
for liso, o script **estende o fundo** com a cor dele e centraliza de verdade.
Numa foto sobre feltro preto isso é invisível: a área inventada é indistinguível
do feltro que já estava lá.

Ele desiste de estender, e aceita sair torto, quando o fundo não é uniforme ou
quando o remendo passaria de 30% da célula. Desligue com `--sem-preencher`.

A cor do fundo é medida pela **mediana** das quatro bordas, não pela média. Isso
importa: quando o item encosta numa borda, ele suja aquela faixa inteira, e com
média o script concluía "fundo irregular" e desistia — era exatamente o que
deixava uma célula em nove visivelmente torta.

Três detalhes que fazem o detector funcionar:

- ele usa **a maior mancha conectada**, não a caixa de tudo que é claro. Sem isso,
  um respingo de luz no canto estica a caixa e engole meia foto;
- o piso de detecção é 0,4% do quadro, não 4%. Miniatura fotografada de longe
  ocupa 2% e ainda assim é o assunto;
- ele nunca amplia além do 1:1 do original, senão a célula sai borrada.

Se o detector não convencer, ele cai sozinho no corte central — que é o
comportamento honesto quando não dá para ter certeza.

**Fundo liso ajuda muito.** O detector compara o objeto com a cor das bordas da
foto, então feltro preto uniforme dá quase 100% de acerto. Fundo bagunçado
derruba a taxa e você vai querer `--corte centro`.

## Numeração

O número no canto de cada célula não é enfeite: ele deixa você escrever na
legenda "o 04 e o 07 estão à venda" sem descrever qual é qual. Numa folha com
nove itens, isso é a diferença entre um post que vende e um post que só é bonito.
