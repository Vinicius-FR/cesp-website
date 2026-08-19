#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
post.py — os outros tipos de post da CESP.

O folha.py cuida da colagem. Este cuida do resto:

    foto      uma foto só, com nome e ficha        (acervo, venda)
    ficha     foto menor + tabela de dados
    software  saída de terminal, sem foto
    capa      capa de carrossel, só tipografia

Compartilha o chrome com o folha.py — mesma medida, mesma barra de mana, mesmo
rodapé — importando de lá em vez de duplicar.

    python3 post.py foto item.jpg --cat U --caminho "~/cards" \\
        --cmd "open lotus-alpha.jpg" --titulo "Black Lotus" \\
        --meta "Alpha · 1993 · acervo pessoal" --selo "não à venda"
"""
import argparse
import os
import sys
from PIL import Image, ImageDraw

from folha import (M, TEMAS, ORDEM_MANA, VERMELHO_PRECO, AQUI,
                   fonte, alt_texto, encaixar, mistura)


def quebrar(d, texto, f, largura):
    """Quebra em linhas que caibam na largura dada."""
    linhas, atual = [], ""
    for palavra in texto.split():
        teste = (atual + " " + palavra).strip()
        if d.textlength(teste, font=f) <= largura or not atual:
            atual = teste
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def montar(cfg):
    W = cfg.tam
    t = TEMAS[cfg.tema]
    m = {k: v * W for k, v in M.items()}
    img = Image.new("RGB", (W, W), t["fundo"])
    d = ImageDraw.Draw(img)
    borda = mistura(t["fundo"], t["fosforo"], t["borda_a"])
    lw = max(1, int(round(m["borda"])))
    esq, dir_ = m["pad"], W - m["pad_dir"]
    util = dir_ - esq

    tam_tit = m["tit"] * (1.7 if cfg.tipo == "capa" else 1.0)
    f_cmd = fonte("JetBrainsMono.ttf", int(m["cmd"]), "Regular")
    f_tit = fonte("JetBrainsMono.ttf", int(tam_tit), "ExtraBold")
    f_met = fonte("JetBrainsMono.ttf", int(m["meta"]), "Regular")
    f_sel = fonte("Silkscreen-Regular.ttf", int(m["selo"]))
    f_prc = fonte("JetBrainsMono.ttf", int(m["preco"]), "ExtraBold")

    # ---- rodapé ----
    marca = None
    cam = os.path.join(AQUI, "assets", "marca-nome.png")
    if os.path.exists(cam):
        mk = Image.open(cam).convert("RGBA")
        marca_h = m["marca"] * mk.height / mk.width
        marca = mk.resize((int(m["marca"]), int(marca_h)), Image.LANCZOS)
    else:
        marca_h = m["tit"] * 0.6
    rod_h = m["pad_rod"] + marca_h

    # ---- blocos de baixo ----
    lin_tit = quebrar(d, cfg.titulo, f_tit, util) if cfg.titulo else []
    alt_lin = tam_tit * 1.12
    h_tit = alt_lin * len(lin_tit)
    h_met = alt_texto(d, cfg.meta, f_met) if cfg.meta else 0
    h_dados = 0
    if cfg.tipo == "ficha" and cfg.dado:
        h_dados = m["meta"] * 1.95 * len(cfg.dado) + m["vao_meta"]
    baixo = h_tit + (m["vao_meta"] + h_met if cfg.meta else 0) + h_dados \
        + m["vao_rod"] + rod_h

    # ---- linha de comando ----
    y = m["pad"]
    prompt = "{}$ ".format(cfg.caminho) if cfg.caminho else "$ "
    d.text((esq, y), prompt, font=f_cmd, fill=t["fraco"])
    d.text((esq + d.textlength(prompt, font=f_cmd), y), cfg.cmd,
           font=f_cmd, fill=t["fosforo"])
    topo = y + alt_texto(d, prompt + cfg.cmd, f_cmd) * 1.35 + m["vao_cmd"]

    # ---- corpo ----
    corpo_h = (W - m["pad"] - baixo) - topo
    if corpo_h < W * 0.12:
        sys.exit("erro: sobrou pouco espaço. Encurte o título ou tire linhas.")

    if cfg.tipo in ("foto", "ficha"):
        if cfg.tipo == "ficha":
            corpo_h *= 0.66
        if cfg.foto:
            with Image.open(cfg.foto) as src:
                img.paste(encaixar(src, int(util), int(corpo_h), cfg.corte,
                                   cfg.margem, cfg.preencher), (int(esq), int(topo)))
        else:
            f_ph = fonte("Silkscreen-Regular.ttf", int(m["selo"]))
            b = d.textbbox((0, 0), "PHOTO", font=f_ph)
            d.text((esq + (util - (b[2] - b[0])) / 2 - b[0],
                    topo + (corpo_h - (b[3] - b[1])) / 2 - b[1]),
                   "PHOTO", font=f_ph, fill=t["fraco"])
        d.rectangle([esq, topo, dir_ - 1, topo + corpo_h - 1], outline=borda, width=lw)

    elif cfg.tipo == "software":
        yy = topo + m["meta"] * 0.4
        for linha in cfg.linha:
            rot, _, estado = linha.partition("|")
            d.text((esq, yy), rot, font=f_met, fill=t["fraco"])
            if estado:
                cor = t["mana"]["G"] if estado.strip().lower() in ("ok", "done") else t["fosforo"]
                d.text((esq + util * 0.62, yy), estado.strip(), font=f_met, fill=cor)
            yy += m["meta"] * 1.85

    elif cfg.tipo == "capa":
        f_frase = fonte("JetBrainsMono.ttf", int(m["tit"] * 1.7), "ExtraBold")
        linhas = quebrar(d, cfg.frase, f_frase, util)
        alt = m["tit"] * 1.7 * 1.1
        yy = topo + (corpo_h - alt * len(linhas)) / 2
        for l in linhas:
            d.text((esq, yy), l, font=f_frase, fill=t["titulo"])
            yy += alt

    # ---- título, meta, dados ----
    y = W - m["pad"] - baixo
    if cfg.tipo != "capa":
        for l in lin_tit:
            d.text((esq, y), l, font=f_tit, fill=t["titulo"])
            y += alt_lin
        if cfg.meta:
            y += m["vao_meta"]
            d.text((esq, y), cfg.meta, font=f_met, fill=t["fraco"])
            y += h_met
    if cfg.tipo == "ficha" and cfg.dado:
        y += m["vao_meta"]
        for par in cfg.dado:
            chave, _, valor = par.partition("=")
            d.text((esq, y), chave, font=f_met, fill=t["fraco"])
            larg = d.textlength(valor, font=f_met)
            d.text((dir_ - larg, y), valor, font=f_met, fill=t["titulo"])
            yl = y + m["meta"] * 1.5
            d.line([(esq, yl), (dir_, yl)], fill=borda, width=1)
            y += m["meta"] * 1.95

    # ---- rodapé ----
    y_linha = y + m["vao_rod"]
    d.line([(esq, y_linha), (dir_, y_linha)], fill=borda, width=lw)
    y_c = y_linha + m["pad_rod"]
    if marca is not None:
        tinta = Image.new("RGBA", marca.size, t["fosforo"] + (255,))
        tinta.putalpha(marca.split()[3])
        img.paste(tinta, (int(esq), int(y_c)), tinta)

    if cfg.preco:
        b = d.textbbox((0, 0), cfg.preco, font=f_prc)
        pw, ph = b[2] - b[0], b[3] - b[1]
        px = dir_ - pw - m["preco"] * 0.9
        py = y_c + (marca_h - ph) / 2 - m["preco"] * 0.34
        d.rectangle([px, py, px + pw + m["preco"] * 0.9, py + ph + m["preco"] * 0.68],
                    fill=VERMELHO_PRECO)
        d.text((px + m["preco"] * 0.45 - b[0], py + m["preco"] * 0.34 - b[1]),
               cfg.preco, font=f_prc, fill=(10, 12, 10))
    else:
        rot = cfg.pagina if cfg.pagina else cfg.selo
        if rot:
            texto = rot if cfg.pagina else rot.upper()
            b = d.textbbox((0, 0), texto, font=f_sel)
            d.text((dir_ - (b[2] - b[0]), y_c + (marca_h - (b[3] - b[1])) / 2),
                   texto, font=f_sel, fill=t["fraco"])

    # ---- barra de mana ----
    seg = W / float(len(ORDEM_MANA))
    for i, cod in enumerate(ORDEM_MANA):
        cor = t["mana"][cod]
        if cod not in cfg.cat:
            cor = mistura(t["fundo"], cor, t["apagado"])
        d.rectangle([W - m["mana"], i * seg, W, (i + 1) * seg], fill=cor)
        if cod == "W" and cod in cfg.cat and cfg.tema == "claro":
            d.rectangle([W - m["mana"], i * seg, W - 1, (i + 1) * seg - 1],
                        outline=t["titulo"], width=lw)
    return img


def principal():
    p = argparse.ArgumentParser(description="Gera os posts da CESP que não são colagem.")
    p.add_argument("tipo", choices=["foto", "ficha", "software", "capa"])
    p.add_argument("foto", nargs="?", default=None)
    p.add_argument("--cat", default="U")
    p.add_argument("--caminho", default="~/cards")
    p.add_argument("--cmd", default="open item.jpg")
    p.add_argument("--titulo", default="")
    p.add_argument("--meta", default="")
    p.add_argument("--selo", default="")
    p.add_argument("--preco", default="")
    p.add_argument("--frase", default="", help="texto grande da capa de carrossel")
    p.add_argument("--pagina", default="", help='ex: "1 / 7 →"')
    p.add_argument("--linha", action="append", default=[],
                   help='linha de saída do software, formato "texto|ok"')
    p.add_argument("--dado", action="append", default=[],
                   help='linha da ficha, formato "peças=1254"')
    p.add_argument("--tema", default="escuro", choices=sorted(TEMAS))
    p.add_argument("--corte", default="auto", choices=["auto", "centro", "topo"])
    p.add_argument("--margem", type=float, default=0.20)
    p.add_argument("--sem-preencher", dest="preencher", action="store_false")
    p.add_argument("--tam", type=int, default=1080)
    p.add_argument("--saida", default="post.png")
    cfg = p.parse_args()

    cfg.cat = [c.strip().upper() for c in cfg.cat.split(",") if c.strip()]
    ruins = [c for c in cfg.cat if c not in ORDEM_MANA]
    if ruins:
        sys.exit("erro: categoria desconhecida {}. Use W,U,B,R,G,I".format(ruins))
    if len(cfg.cat) > 3:
        sys.exit("erro: no máximo 3 categorias acesas — acima disso a barra vira arco-íris.")
    if cfg.tipo in ("foto", "ficha") and not cfg.foto:
        print("aviso: sem foto — gerando o quadro vazio como template. "
              "Rode de novo passando o arquivo quando fotografar.")
    if cfg.tipo == "capa" and not cfg.frase:
        sys.exit("erro: o tipo 'capa' precisa de --frase.")

    montar(cfg).save(cfg.saida)
    print("gravei", cfg.saida)


if __name__ == "__main__":
    principal()
