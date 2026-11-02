
import re


def carregar_letras(caminho):
    letras = []

    with open(caminho, "r", encoding="utf-8") as arquivo:

        for linha in arquivo:

            resultado = re.match(
                r"\[(\d+):(\d+(?:\.\d+)?)\](.*)",
                linha.strip()
            )

            if resultado:

                minutos = int(resultado.group(1))
                segundos = float(resultado.group(2))
                texto = resultado.group(3).strip()

                tempo = (minutos * 60 + segundos) * 1000

                letras.append({
                    "tempo": int(tempo),
                    "texto": texto
                })

    letras.sort(key=lambda item: item["tempo"])

    return letras


def encontrar_linha_atual(letras, tempo_atual):

    linha_atual = -1

    for indice, linha in enumerate(letras):

        if tempo_atual >= linha["tempo"]:
            linha_atual = indice

        else:
            break

    return linha_atual

