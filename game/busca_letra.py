
import os
import re
import time
import unicodedata
from difflib import SequenceMatcher

import requests
from mutagen import File as MutagenFile


API = "https://lrclib.net/api"

HEADERS = {
    "User-Agent": "TypeBeat/1.0 (Personal Desktop Music Game)"
}


# ==========================================
# NORMALIZAR TEXTO
# ==========================================

def normalizar(texto):

    texto = str(texto or "").casefold()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"[^a-z0-9]", "", texto)

    return texto


# ==========================================
# LIMPAR TÍTULO
# ==========================================

def limpar_titulo(texto):

    texto = str(texto or "").strip()

    # Remover informações extras comuns nos nomes dos arquivos.

    padroes = [
        r"\s*[\(\[]official music video[\)\]]",
        r"\s*[\(\[]official lyric video[\)\]]",
        r"\s*[\(\[]official video[\)\]]",
        r"\s*[\(\[]lyrics?[\)\]]",
        r"\s*[\(\[]audio[\)\]]",
        r"\s*[\(\[]visualizer[\)\]]",
        r"\s*[\(\[]hd[\)\]]",
        r"\s*[\(\[]4k[\)\]]",
    ]

    for padrao in padroes:

        texto = re.sub(
            padrao,
            "",
            texto,
            flags=re.IGNORECASE
        )

    return texto.strip(" -_.")


# ==========================================
# EXTRAIR ARTISTA E TÍTULO
# ==========================================

def separar_artista_titulo(texto):

    texto = limpar_titulo(texto)

    separadores = [
        " - ",
        " – ",
        " — "
    ]

    for separador in separadores:

        if separador in texto:

            artista, titulo = texto.split(
                separador,
                1
            )

            artista = artista.strip()
            titulo = limpar_titulo(titulo)

            if artista and titulo:
                return artista, titulo

    return "", texto


# ==========================================
# OBTER METADADOS
# ==========================================

def obter_metadados(caminho):

    nome_arquivo = os.path.splitext(
        os.path.basename(caminho)
    )[0]

    artista = ""
    titulo = ""

    duracao = None

    try:

        audio = MutagenFile(
            caminho,
            easy=True
        )

        if audio:

            if audio.info:
                duracao = int(audio.info.length)

            tags = audio.tags or {}

            titulo_tags = tags.get("title", [""])
            artista_tags = tags.get("artist", [""])

            if titulo_tags:
                titulo = str(titulo_tags[0]).strip()

            if artista_tags:
                artista = str(artista_tags[0]).strip()

    except Exception as erro:

        print("Erro ao ler metadados:", erro)

    # Se o artista não veio dos metadados,
    # tentar identificar pelo nome do arquivo.

    artista_arquivo, titulo_arquivo = separar_artista_titulo(
        nome_arquivo
    )

    if not artista:
        artista = artista_arquivo

    if not titulo:
        titulo = titulo_arquivo

    # Se o título dos metadados também contém
    # "Artista - Música", separar corretamente.

    if titulo:

        artista_embutido, titulo_limpo = separar_artista_titulo(
            titulo
        )

        if artista_embutido:

            if not artista:
                artista = artista_embutido

            titulo = titulo_limpo

    # Se ainda não temos título, usar o nome do arquivo.

    if not titulo:
        titulo = limpar_titulo(nome_arquivo)

    # Limitar duração para evitar valores inválidos.

    if duracao is not None:

        if duracao < 1 or duracao > 3600:
            duracao = None

    return {
        "titulo": limpar_titulo(titulo),
        "artista": artista,
        "duracao": duracao
    }


# ==========================================
# CONSULTAR API COM NOVAS TENTATIVAS
# ==========================================

def consultar_api(endpoint, parametros=None):

    url = API + endpoint

    ultimo_erro = None

    for tentativa in range(3):

        try:

            resposta = requests.get(
                url,
                params=parametros,
                headers=HEADERS,
                timeout=15
            )

            if resposta.status_code == 404:
                return None

            # Erros temporários: tentar novamente.

            if resposta.status_code in (429, 500, 502, 503, 504):

                ultimo_erro = (
                    f"Erro temporário da LRCLIB: "
                    f"{resposta.status_code}"
                )

                if tentativa < 2:

                    espera = 2 ** tentativa

                    print(
                        f"API indisponível. "
                        f"Nova tentativa em {espera} segundos..."
                    )

                    time.sleep(espera)

                    continue

                raise Exception(ultimo_erro)

            resposta.raise_for_status()

            return resposta.json()

        except requests.exceptions.Timeout:

            ultimo_erro = "Tempo limite da consulta excedido."

            if tentativa < 2:
                time.sleep(2 ** tentativa)
                continue

        except requests.exceptions.ConnectionError:

            ultimo_erro = "Falha na conexão com a LRCLIB."

            if tentativa < 2:
                time.sleep(2 ** tentativa)
                continue

        except requests.exceptions.HTTPError as erro:

            raise Exception(
                f"Erro HTTP na LRCLIB: {erro}"
            )

    raise Exception(
        ultimo_erro or "Não foi possível consultar a LRCLIB."
    )


# ==========================================
# COMPARAR RESULTADOS
# ==========================================

def calcular_pontuacao(
    resultado,
    titulo_procurado,
    artista_procurado,
    duracao_procurada
):

    titulo_resultado = resultado.get(
        "trackName",
        ""
    )

    artista_resultado = resultado.get(
        "artistName",
        ""
    )

    titulo_a = normalizar(titulo_procurado)
    titulo_b = normalizar(titulo_resultado)

    artista_a = normalizar(artista_procurado)
    artista_b = normalizar(artista_resultado)

    if not titulo_a or not titulo_b:
        return 0

    nota_titulo = SequenceMatcher(
        None,
        titulo_a,
        titulo_b
    ).ratio()

    nota_artista = 0

    if artista_a and artista_b:

        nota_artista = SequenceMatcher(
            None,
            artista_a,
            artista_b
        ).ratio()

    # Título tem maior peso.

    if artista_a:

        pontuacao = (
            nota_titulo * 0.75
            + nota_artista * 0.25
        )

    else:

        pontuacao = nota_titulo

    # Bônus por duração próxima.

    duracao_resultado = resultado.get("duration")

    if duracao_procurada and duracao_resultado:

        diferenca = abs(
            duracao_procurada - duracao_resultado
        )

        if diferenca <= 3:
            pontuacao += 0.15

        elif diferenca <= 10:
            pontuacao += 0.08

        elif diferenca > 30:
            pontuacao -= 0.10

    return pontuacao


# ==========================================
# BUSCAR LETRA
# ==========================================

def buscar_letra(caminho):

    musica = obter_metadados(caminho)

    titulo = musica["titulo"]
    artista = musica["artista"]
    duracao = musica["duracao"]

    print("\n========== TYPEBEAT ==========")

    print("Título:", titulo)
    print("Artista:", artista)
    print("Duração:", duracao, "segundos")

    if not titulo:
        raise Exception(
            "Não foi possível identificar o título da música."
        )

    # ======================================
    # PRIMEIRA TENTATIVA: BUSCA EXATA
    # ======================================

    if artista:

        print("Tentando busca exata...")

        parametros = {
            "track_name": titulo,
            "artist_name": artista
        }

        if duracao:
            parametros["duration"] = duracao

        try:

            resultado = consultar_api(
                "/get",
                parametros
            )

            if resultado:

                letra = resultado.get("syncedLyrics")

                if letra:

                    print("Letra encontrada na busca exata!")

                    return letra, musica

                print(
                    "A música foi encontrada, "
                    "mas não possui letra sincronizada."
                )

        except Exception as erro:

            print(
                "Falha na busca exata:",
                erro
            )

    else:

        print(
            "Artista desconhecido. "
            "Pulando busca exata."
        )

    # ======================================
    # SEGUNDA TENTATIVA: BUSCA ALTERNATIVA
    # ======================================

    consultas = []

    consultas.append({
        "q": titulo
    })

    consultas.append({
        "track_name": titulo
    })

    if artista:

        consultas.append({
            "track_name": titulo,
            "artist_name": artista
        })

        consultas.append({
            "q": artista + " " + titulo
        })

    resultados = []

    for parametros in consultas:

        print(
            "Tentando busca alternativa:",
            parametros
        )

        try:

            resposta = consultar_api(
                "/search",
                parametros
            )

            if resposta:

                resultados.extend(resposta)

        except Exception as erro:

            print(
                "Falha na busca alternativa:",
                erro
            )

    # ======================================
    # REMOVER RESULTADOS DUPLICADOS
    # ======================================

    resultados_unicos = {}

    for resultado in resultados:

        chave = (
            normalizar(resultado.get("trackName", "")),
            normalizar(resultado.get("artistName", ""))
        )

        resultados_unicos[chave] = resultado

    resultados = list(
        resultados_unicos.values()
    )

    if not resultados:

        raise Exception(
            "Nenhum resultado encontrado na LRCLIB. "
            "A API pode estar indisponível ou a música "
            "pode não estar cadastrada."
        )

    # ======================================
    # CLASSIFICAR RESULTADOS
    # ======================================

    candidatos = []

    for resultado in resultados:

        letra = resultado.get("syncedLyrics")

        # O TypeBeat precisa de letras sincronizadas.

        if not letra:
            continue

        pontuacao = calcular_pontuacao(
            resultado,
            titulo,
            artista,
            duracao
        )

        candidatos.append((
            pontuacao,
            resultado
        ))

    if not candidatos:

        raise Exception(
            "Encontramos resultados para a música, "
            "mas nenhum possui letra sincronizada."
        )

    candidatos.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # ======================================
    # ESCOLHER MELHOR RESULTADO
    # ======================================

    melhor_pontuacao, melhor_resultado = candidatos[0]

    print("\nMelhor resultado:")

    print(
        "Título:",
        melhor_resultado.get("trackName")
    )

    print(
        "Artista:",
        melhor_resultado.get("artistName")
    )

    print(
        "Pontuação:",
        round(melhor_pontuacao, 2)
    )

    # Evitar escolher uma música muito diferente.

    if melhor_pontuacao < 0.55:

        raise Exception(
            "Os resultados encontrados não correspondem "
            "com segurança à música selecionada."
        )

    letra = melhor_resultado.get("syncedLyrics")

    if not letra:

        raise Exception(
            "O resultado selecionado não possui letra sincronizada."
        )

    print("\nLetra encontrada com sucesso!")

    return letra, musica
