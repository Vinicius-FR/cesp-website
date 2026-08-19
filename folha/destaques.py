#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
destaques.py — capas dos destaques do Instagram, uma por categoria.

Capa de destaque aparece a ~64 px de diâmetro. Nesse tamanho nome de pasta
não lê, então quem carrega a identificação é a letra de mana, enorme, na cor
da categoria. O nome vai embaixo em corpo pequeno, para quem abrir o perfil
no computador.
"""
from PIL import Image, ImageDraw
from folha import TEMAS, fonte

CATS = [("U", "cards"), ("R", "cars"), ("B", "comics"),
        ("W", "blocks"), ("G", "games"), ("I", "apps")]
LADO = 1080
t = TEMAS["escuro"]

for cod, nome in CATS:
    img = Image.new("RGB", (LADO, LADO), t["fundo"])
    d = ImageDraw.Draw(img)
    cor = t["mana"][cod]

    # anel: o símbolo de mana é um círculo, e ele também avisa onde o
    # Instagram vai cortar
    cy_anel = LADO * 0.44
    r = LADO * 0.27
    d.ellipse([LADO/2 - r, cy_anel - r, LADO/2 + r, cy_anel + r],
              outline=tuple(int(c * 0.45) for c in cor), width=int(LADO * 0.013))

    f_letra = fonte("JetBrainsMono.ttf", int(LADO * 0.30), "ExtraBold")
    b = d.textbbox((0, 0), cod, font=f_letra)
    d.text(((LADO - (b[2] - b[0])) / 2 - b[0], cy_anel - (b[3] - b[1]) / 2 - b[1]),
           cod, font=f_letra, fill=cor)

    f_nome = fonte("Silkscreen-Regular.ttf", int(LADO * 0.058))
    b = d.textbbox((0, 0), nome, font=f_nome)
    d.text(((LADO - (b[2] - b[0])) / 2 - b[0], LADO * 0.80 - b[1]),
           nome, font=f_nome, fill=t["fosforo"])

    img.save("destaque-{}.png".format(nome))
    print("gravei destaque-{}.png".format(nome))
