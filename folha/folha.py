#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
folha.py — monta post de colagem da CESP a partir de fotos soltas.

Mesma lógica do compositor de tokens: as medidas do chrome são frações da
largura do quadro, então a mesma conta serve para 1080 px de Instagram e para
2160 px de arquivo. Nada é posicionado em pixel absoluto.

    python3 folha.py fotos/ --layout 3x3 --cat U,R,G \\
        --caminho "~/cars" --cmd "montage *.jpg -tile 3x3" \\
        --titulo "Coleção F1 · 1988—1994" \\
        --meta "9 miniaturas · 1:43 · o 04 e o 07 estão à venda" \\
        --selo acervo --saida post.png

Depende só de Pillow.  pip install pillow
"""
import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops, ImageStat

AQUI = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------
# medidas: tudo em fração da largura do quadro
# --------------------------------------------------------------------------
M = {
    "pad": 0.050, "pad_dir": 0.075, "mana": 0.027,
    "cmd": 0.031, "vao_cmd": 0.034, "vao_cel": 0.010,
    "tit": 0.050, "meta": 0.029, "vao_meta": 0.014,
    "vao_rod": 0.034, "pad_rod": 0.026, "marca": 0.145,
    "selo": 0.024, "num": 0.020, "borda": 0.0032, "preco": 0.036,
}

TEMAS = {
    "escuro": {"fundo": (10, 12, 10), "fosforo": (124, 231, 140),
               "fraco": (78, 158, 98), "titulo": (239, 239, 234),
               "borda_a": 0.20, "apagado": 0.20,
               "mana": {"W": (255, 251, 213), "U": (88, 182, 255), "B": (110, 122, 140),
                        "R": (255, 91, 91), "G": (0, 229, 82), "I": (206, 148, 64)}},
    "claro":  {"fundo": (239, 239, 234), "fosforo": (22, 24, 29),
               "fraco": (105, 108, 115), "titulo": (22, 24, 29),
               "borda_a": 0.18, "apagado": 0.24,
               "mana": {"W": (199, 195, 179), "U": (14, 104, 171), "B": (22, 24, 29),
                        "R": (211, 32, 42), "G": (0, 115, 62), "I": (172, 112, 48)}},
}

ORDEM_MANA = ["W", "U", "B", "R", "G", "I"]
VERMELHO_PRECO = (255, 91, 91)

# --------------------------------------------------------------------------
# layouts: (linhas como lista de (peso, n_de_celulas))
# --------------------------------------------------------------------------
LAYOUTS = {
    "3x3":  [(1, 3), (1, 3), (1, 3)],
    "3x2":  [(1, 3), (1, 3)],
    "2x2":  [(1, 2), (1, 2)],
    "hero": [(2.3, 1), (1, 4)],
}


def celulas(layout, x, y, w, h, vao):
    """Devolve retângulos (x, y, w, h) na ordem de leitura."""
    linhas = LAYOUTS[layout]
    peso = sum(p for p, _ in linhas)
    alt_util = h - vao * (len(linhas) - 1)
    rects, cy = [], y
    for p, n in linhas:
        lh = alt_util * p / peso
        lw = (w - vao * (n - 1)) / n
        for i in range(n):
            rects.append((x + i * (lw + vao), cy, lw, lh))
        cy += lh + vao
    return rects


# --------------------------------------------------------------------------
# fontes
# --------------------------------------------------------------------------
def fonte(nome, tamanho, peso=None):
    caminhos = [os.path.join(AQUI, "fontes", nome), os.path.join("fontes", nome), nome]
    for c in caminhos:
        try:
            f = ImageFont.truetype(c, tamanho)
            if peso:
                try:
                    f.set_variation_by_name(peso)
                except Exception:
                    pass
            return f
        except Exception:
            continue
    for alt in ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                "/System/Library/Fonts/Menlo.ttc", "C:/Windows/Fonts/consola.ttf"]:
        if os.path.exists(alt):
            return ImageFont.truetype(alt, tamanho)
    return ImageFont.load_default()


def alt_texto(d, txt, f):
    if not txt:
        return 0
    b = d.textbbox((0, 0), txt, font=f)
    return b[3] - b[1]


# --------------------------------------------------------------------------
# preparo das fotos
# --------------------------------------------------------------------------
def maior_mancha(mask):
    """
    Caixa da maior mancha conectada. Sem isso, qualquer respingo claro no
    canto — etiqueta, poeira, reflexo — entra na conta e estica a caixa
    até englobar meia foto.
    """
    w, h = mask.size
    px = mask.load()
    visto = bytearray(w * h)
    melhor, melhor_n = None, 0
    for y0 in range(h):
        for x0 in range(w):
            i0 = y0 * w + x0
            if visto[i0] or not px[x0, y0]:
                continue
            pilha, n = [i0], 0
            visto[i0] = 1
            x_min = x_max = x0
            y_min = y_max = y0
            while pilha:
                i = pilha.pop()
                x, y = i % w, i // w
                n += 1
                if x < x_min: x_min = x
                if x > x_max: x_max = x
                if y < y_min: y_min = y
                if y > y_max: y_max = y
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h:
                        j = ny * w + nx
                        if not visto[j] and px[nx, ny]:
                            visto[j] = 1
                            pilha.append(j)
            if n > melhor_n:
                melhor_n, melhor = n, (x_min, y_min, x_max + 1, y_max + 1)
    return melhor


def cor_de_fundo(im, faixa=0.04):
    """Cor média das quatro bordas e o quanto elas variam entre si."""
    p = im.convert("RGB").resize((160, max(1, int(160 * im.height / im.width))))
    w, h = p.size
    f = max(2, int(min(w, h) * faixa))
    tiras = [p.crop((0, 0, w, f)), p.crop((0, h - f, w, h)),
             p.crop((0, 0, f, h)), p.crop((w - f, 0, w, h))]
    medias = [ImageStat.Stat(t).mean[:3] for t in tiras]
    desvios = [ImageStat.Stat(t).stddev[:3] for t in tiras]

    def mediana(v):
        v = sorted(v)
        return (v[len(v) // 2] + v[(len(v) - 1) // 2]) / 2.0

    # Mediana, não média nem máximo: quando o objeto encosta numa borda, ele
    # suja aquela faixa inteira. Com média/máximo, uma faixa contaminada faz o
    # script concluir "fundo irregular" e desistir de centralizar — foi o que
    # aconteceu na célula 02 do exemplo.
    cor = tuple(int(round(mediana([m[i] for m in medias]))) for i in range(3))
    entre = max(mediana([abs(m[i] - cor[i]) for m in medias]) for i in range(3))
    espalha = mediana([max(dv) for dv in desvios])
    return cor, max(espalha, entre)


def recorte_assunto(im, tol=26):
    """Acha o assunto comparando com a cor das bordas. None se não convencer."""
    p = im.convert("L").resize((200, max(1, int(200 * im.height / im.width))))
    w, h = p.size
    faixa = 4
    bordas = (p.crop((0, 0, w, faixa)), p.crop((0, h - faixa, w, h)),
              p.crop((0, 0, faixa, h)), p.crop((w - faixa, 0, w, h)))
    fundo = sum(ImageStat.Stat(b).mean[0] for b in bordas) / 4.0
    dif = ImageChops.difference(p, Image.new("L", p.size, int(fundo)))
    mask = dif.point(lambda v: 255 if v > tol else 0)
    bb = maior_mancha(mask)
    if not bb:
        return None
    area = (bb[2] - bb[0]) * (bb[3] - bb[1]) / float(w * h)
    # o piso tem que ser baixo: miniatura fotografada de longe ocupa 2% do quadro
    # e ainda assim é o assunto. O teto é que importa — acima disso não achou nada,
    # achou a cena inteira, e aí o corte central é mais honesto.
    if area < 0.004 or area > 0.90:
        return None
    ex, ey = im.width / float(w), im.height / float(h)
    return (bb[0] * ex, bb[1] * ey, bb[2] * ex, bb[3] * ey)


def encaixar(im, lw, lh, modo="centro", margem=0.20, preencher=True):
    """
    Corta na proporção da célula e redimensiona.

    No modo auto o corte APROXIMA no assunto, não só ajusta a proporção:
    sem isso, foto de celular 4:3 virando célula 3:2 perde tão pouca área
    que o item continua perdido no meio do feltro. A aproximação é limitada
    para nunca ampliar além do 1:1 da origem, senão a célula sai borrada.
    """
    im = ImageOps.exif_transpose(im).convert("RGB")
    alvo = lw / float(lh)
    cw = ch = None

    if modo == "auto":
        bb = recorte_assunto(im)
        if bb:
            x0, y0, x1, y1 = bb
            folga = max(x1 - x0, y1 - y0) * margem
            x0, y0, x1, y1 = x0 - folga, y0 - folga, x1 + folga, y1 + folga
            bw, bh = x1 - x0, y1 - y0
            if bw / bh > alvo:
                bh = bw / alvo
            else:
                bw = bh * alvo
            cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
            cw, ch = bw, bh
            if cw < lw:                      # nunca ampliar além do original
                cw, ch = float(lw), float(lh)

            # Se a janela passa da beirada da foto, ela normalmente trava ali e o
            # assunto sai torto — foi exatamente o que apareceu nas células 02, 04,
            # 05 e 08 do primeiro exemplo. Quando o fundo é liso (feltro), dá para
            # estender o fundo e centralizar de verdade, sem custo visual.
            esq = max(0.0, cw / 2.0 - cx)
            cima = max(0.0, ch / 2.0 - cy)
            dir_ = max(0.0, cx + cw / 2.0 - im.width)
            baixo = max(0.0, cy + ch / 2.0 - im.height)
            falta = esq + cima + dir_ + baixo
            if falta > 0 and preencher:
                cor, variacao = cor_de_fundo(im)
                inventado = ((cw * (cima + baixo)) + (ch * (esq + dir_))) / (cw * ch)
                # fundo bagunçado ou remendo grande demais: melhor sair torto
                if variacao <= 14 and inventado <= 0.60:
                    b = (int(esq) + 1, int(cima) + 1, int(dir_) + 1, int(baixo) + 1)
                    im = ImageOps.expand(im, border=b, fill=cor)
                    cx, cy = cx + b[0], cy + b[1]

            k = min(1.0, im.width / cw, im.height / ch)
            cw, ch = cw * k, ch * k

    if cw is None:
        cx, cy = im.width / 2.0, im.height / 2.0
        if modo == "topo":
            cy = im.height * 0.34
        if im.width / float(im.height) > alvo:
            ch = float(im.height)
            cw = ch * alvo
        else:
            cw = float(im.width)
            ch = cw / alvo

    x = min(max(cx - cw / 2.0, 0), im.width - cw)
    y = min(max(cy - ch / 2.0, 0), im.height - ch)
    corte = im.crop((int(x), int(y), int(x + cw), int(y + ch)))
    return corte.resize((int(round(lw)), int(round(lh))), Image.LANCZOS)


def mistura(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# --------------------------------------------------------------------------
# montagem
# --------------------------------------------------------------------------
def montar(fotos, cfg):
    W = cfg.tam
    t = TEMAS[cfg.tema]
    m = {k: v * W for k, v in M.items()}
    img = Image.new("RGB", (W, W), t["fundo"])
    d = ImageDraw.Draw(img)

    f_cmd = fonte("JetBrainsMono.ttf", int(m["cmd"]), "Regular")
    f_tit = fonte("JetBrainsMono.ttf", int(m["tit"]), "ExtraBold")
    f_met = fonte("JetBrainsMono.ttf", int(m["meta"]), "Regular")
    f_sel = fonte("Silkscreen-Regular.ttf", int(m["selo"]))
    f_num = fonte("Silkscreen-Bold.ttf", int(m["num"]))
    f_prc = fonte("JetBrainsMono.ttf", int(m["preco"]), "ExtraBold")

    borda = mistura(t["fundo"], t["fosforo"], t["borda_a"])

    # ---- rodapé (medido de baixo para cima) ----
    marca_w = m["marca"]
    marca = None
    cam_marca = os.path.join(AQUI, "assets", "marca-nome.png")
    if os.path.exists(cam_marca):
        mk = Image.open(cam_marca).convert("RGBA")
        marca_h = marca_w * mk.height / mk.width
        marca = mk.resize((int(marca_w), int(marca_h)), Image.LANCZOS)
    else:
        marca_h = m["tit"] * 0.6
    rod_h = m["pad_rod"] + marca_h
    y_rod = W - m["pad"] - rod_h

    # ---- blocos de texto de baixo ----
    h_tit = alt_texto(d, cfg.titulo, f_tit) if cfg.titulo else 0
    h_met = alt_texto(d, cfg.meta, f_met) if cfg.meta else 0
    bloco_baixo = h_tit + (m["vao_meta"] + h_met if cfg.meta else 0) + m["vao_rod"] + rod_h

    # ---- linha de comando ----
    y = m["pad"]
    prompt = "{}$ ".format(cfg.caminho) if cfg.caminho else "$ "
    d.text((m["pad"], y), prompt, font=f_cmd, fill=t["fraco"])
    lp = d.textlength(prompt, font=f_cmd)
    d.text((m["pad"] + lp, y), cfg.cmd, font=f_cmd, fill=t["fosforo"])
    h_cmd = alt_texto(d, prompt + cfg.cmd, f_cmd) * 1.35

    # ---- área da colagem ----
    cx = m["pad"]
    cy = y + h_cmd + m["vao_cmd"]
    cw = W - m["pad"] - m["pad_dir"]
    ch = (W - m["pad"] - bloco_baixo) - cy
    if ch < W * 0.2:
        sys.exit("erro: sobrou pouco espaço para as fotos. Encurte o título ou o meta.")

    rects = celulas(cfg.layout, cx, cy, cw, ch, m["vao_cel"])
    lw = max(1, int(round(m["borda"])))

    for i, (rx, ry, rw, rh) in enumerate(rects):
        cx0, cy0 = int(round(rx)), int(round(ry))
        cw0, ch0 = int(round(rw)), int(round(rh))
        if i < len(fotos):
            try:
                with Image.open(fotos[i]) as src:
                    img.paste(encaixar(src, cw0, ch0, cfg.corte, cfg.margem, cfg.preencher), (cx0, cy0))
            except Exception as e:
                print("  ! pulei {}: {}".format(os.path.basename(fotos[i]), e))
        d.rectangle([cx0, cy0, cx0 + cw0 - 1, cy0 + ch0 - 1], outline=borda, width=lw)

        if cfg.numerar:
            n = "{:02d}".format(i + 1)
            b = d.textbbox((0, 0), n, font=f_num)
            pw, ph = b[2] - b[0], b[3] - b[1]
            px, py = cx0 + m["vao_cel"] * 0.6, cy0 + m["vao_cel"] * 0.6
            d.rectangle([px, py, px + pw + m["num"] * 0.7, py + ph + m["num"] * 0.7],
                        fill=t["fundo"])
            d.text((px + m["num"] * 0.35 - b[0], py + m["num"] * 0.35 - b[1]),
                   n, font=f_num, fill=t["fosforo"])

    # ---- título, meta ----
    y = W - m["pad"] - bloco_baixo
    if cfg.titulo:
        d.text((m["pad"], y), cfg.titulo, font=f_tit, fill=t["titulo"])
        y += h_tit
    if cfg.meta:
        y += m["vao_meta"]
        d.text((m["pad"], y), cfg.meta, font=f_met, fill=t["fraco"])
        y += h_met

    # ---- rodapé ----
    y_linha = y + m["vao_rod"]
    d.line([(m["pad"], y_linha), (W - m["pad_dir"], y_linha)], fill=borda, width=lw)
    y_conteudo = y_linha + m["pad_rod"]
    if marca is not None:
        tinta = Image.new("RGBA", marca.size, t["fosforo"] + (255,))
        tinta.putalpha(marca.split()[3])
        img.paste(tinta, (int(m["pad"]), int(y_conteudo)), tinta)
    else:
        d.text((m["pad"], y_conteudo), "CESP", font=f_tit, fill=t["fosforo"])

    if cfg.preco:
        b = d.textbbox((0, 0), cfg.preco, font=f_prc)
        pw, ph = b[2] - b[0], b[3] - b[1]
        px = W - m["pad_dir"] - pw - m["preco"] * 0.9
        py = y_conteudo + (marca_h - ph) / 2 - m["preco"] * 0.34
        d.rectangle([px, py, px + pw + m["preco"] * 0.9, py + ph + m["preco"] * 0.68],
                    fill=VERMELHO_PRECO)
        d.text((px + m["preco"] * 0.45 - b[0], py + m["preco"] * 0.34 - b[1]),
               cfg.preco, font=f_prc, fill=(10, 12, 10))
    elif cfg.selo:
        b = d.textbbox((0, 0), cfg.selo.upper(), font=f_sel)
        d.text((W - m["pad_dir"] - (b[2] - b[0]), y_conteudo + (marca_h - (b[3] - b[1])) / 2),
               cfg.selo.upper(), font=f_sel, fill=t["fraco"])

    # ---- barra de mana ----
    seg = W / float(len(ORDEM_MANA))
    for i, cod in enumerate(ORDEM_MANA):
        cor = t["mana"][cod]
        if cod not in cfg.cat:
            cor = mistura(t["fundo"], cor, t["apagado"])
        d.rectangle([W - m["mana"], i * seg, W, (i + 1) * seg], fill=cor)
        # o branco sobre papel tem só 1,5:1 de contraste: sem filete, some
        if cod == "W" and cod in cfg.cat and cfg.tema == "claro":
            d.rectangle([W - m["mana"], i * seg, W - 1, (i + 1) * seg - 1],
                        outline=t["titulo"], width=max(1, int(m["borda"])))

    return img


# --------------------------------------------------------------------------
def principal():
    p = argparse.ArgumentParser(
        description="Monta post de colagem da CESP a partir de fotos soltas.")
    p.add_argument("pasta", help="pasta com as fotos (ou uma lista de arquivos)", nargs="+")
    p.add_argument("--layout", default="3x3", choices=sorted(LAYOUTS),
                   help="3x3 (9 fotos), 3x2 (6), 2x2 (4), hero (1 grande + 4)")
    p.add_argument("--cat", default="U",
                   help="categorias acesas na barra, separadas por vírgula: W,U,B,R,G,I")
    p.add_argument("--caminho", default="~/cards", help="caminho mostrado no prompt")
    p.add_argument("--cmd", default="montage *.jpg -tile 3x3", help="comando mostrado")
    p.add_argument("--titulo", default="")
    p.add_argument("--meta", default="")
    p.add_argument("--selo", default="", help="texto pequeno à direita no rodapé")
    p.add_argument("--preco", default="", help='ex: "R$ 340,00" — substitui o selo')
    p.add_argument("--tema", default="escuro", choices=sorted(TEMAS))
    p.add_argument("--corte", default="auto", choices=["auto", "centro", "topo"])
    p.add_argument("--margem", type=float, default=0.20,
                   help="folga em volta do assunto no corte automático (0.20 = 20%%)")
    p.add_argument("--tam", type=int, default=1080)
    p.add_argument("--sem-numero", dest="numerar", action="store_false")
    p.add_argument("--sem-preencher", dest="preencher", action="store_false",
                   help="não estende o fundo liso para centralizar item na beirada")
    p.add_argument("--saida", default="post.png")
    cfg = p.parse_args()

    cfg.cat = [c.strip().upper() for c in cfg.cat.split(",") if c.strip()]
    ruins = [c for c in cfg.cat if c not in ORDEM_MANA]
    if ruins:
        sys.exit("erro: categoria desconhecida {}. Use W,U,B,R,G,I".format(ruins))

    exts = (".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".heic")
    fotos = []
    for alvo in cfg.pasta:
        if os.path.isdir(alvo):
            fotos += [os.path.join(alvo, n) for n in sorted(os.listdir(alvo))
                      if n.lower().endswith(exts)]
        elif os.path.isfile(alvo):
            fotos.append(alvo)
    if not fotos:
        print("aviso: nenhuma foto — gerando a grade vazia como template.")

    por_folha = sum(n for _p, n in LAYOUTS[cfg.layout])
    folhas = [fotos[i:i + por_folha] for i in range(0, len(fotos), por_folha)] or [[]]
    print("{} foto(s), {} por folha, {} folha(s)".format(len(fotos), por_folha, len(folhas)))
    if len(fotos) % por_folha and len(folhas) > 1:
        print("  aviso: a última folha fica com {} célula(s) vazia(s)".format(
            por_folha * len(folhas) - len(fotos)))

    base, ext = os.path.splitext(cfg.saida)
    for i, grupo in enumerate(folhas, 1):
        nome = cfg.saida if len(folhas) == 1 else "{}-{:02d}{}".format(base, i, ext)
        montar(grupo, cfg).save(nome)
        print("  gravei", nome)


if __name__ == "__main__":
    principal()
