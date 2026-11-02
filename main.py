
import sys
import os
import tempfile

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QFileDialog
)

from PySide6.QtCore import (
    Qt,
    QUrl,
    QTimer,
    QPropertyAnimation,
    QEasingCurve,
    Property,
    Signal,
    QThread
)

from PySide6.QtGui import QPainter, QColor, QFont

from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from game.letras import carregar_letras, encontrar_linha_atual
from game.busca_letra import buscar_letra


# ==========================================
# BUSCA DE LETRAS EM SEGUNDO PLANO
# ==========================================

class BuscaLetraThread(QThread):

    sucesso = Signal(str, str)
    falha = Signal(str)

    def __init__(self, caminho):
        super().__init__()
        self.caminho = caminho

    def run(self):
        try:
            letra, musica = buscar_letra(self.caminho)

            self.sucesso.emit(
                letra,
                musica["titulo"] + " - " + musica["artista"]
            )

        except Exception as erro:
            self.falha.emit(str(erro))


# ==========================================
# ÁREA DE LETRAS
# ==========================================

class AreaLetras(QWidget):

    def __init__(self):
        super().__init__()

        self.setMinimumHeight(300)
        self.setMaximumHeight(300)

        self.linhas = [
            "",
            "Aguardando a música...",
            ""
        ]

        self.progresso = []

        self._deslocamento = 0.0
        self.altura_linha = 100

        self.animacao = QPropertyAnimation(
            self,
            b"deslocamento"
        )

        self.animacao.setDuration(450)

        self.animacao.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        self.novas_linhas = None
        self.novo_progresso = None

        self.animacao.finished.connect(
            self.finalizar_animacao
        )

    def get_deslocamento(self):
        return self._deslocamento

    def set_deslocamento(self, valor):
        self._deslocamento = valor
        self.update()

    deslocamento = Property(
        float,
        get_deslocamento,
        set_deslocamento
    )

    # ======================================
    # DESENHAR ÁREA DE LETRAS
    # ======================================

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        painter.setRenderHint(
            QPainter.RenderHint.TextAntialiasing
        )

        centro = self.height() / 2

        posicoes = [
            centro - self.altura_linha,
            centro,
            centro + self.altura_linha
        ]

        if self.animacao.state() == QPropertyAnimation.State.Running:

            for i, texto in enumerate(self.linhas):

                y = posicoes[i] - self._deslocamento

                self.desenhar_linha(
                    painter,
                    texto,
                    y,
                    i,
                    self.progresso
                )

            if self.novas_linhas:

                y = (
                    posicoes[2]
                    + self.altura_linha
                    - self._deslocamento
                )

                self.desenhar_linha(
                    painter,
                    self.novas_linhas[2],
                    y,
                    2,
                    []
                )

        else:

            for i, texto in enumerate(self.linhas):

                self.desenhar_linha(
                    painter,
                    texto,
                    posicoes[i],
                    i,
                    self.progresso
                )

    # ======================================
    # DESENHAR UMA LINHA
    # ======================================

    def desenhar_linha(
        self,
        painter,
        texto,
        y,
        indice,
        progresso
    ):

        if not texto:
            return

        fonte = QFont("Arial")

        if indice == 1:
            fonte.setPointSize(25)
            fonte.setBold(True)
        else:
            fonte.setPointSize(19)

        painter.setFont(fonte)

        metricas = painter.fontMetrics()

        margem = 35
        largura_maxima = max(100, self.width() - margem * 2)

        # Quebra o texto respeitando as palavras.

        partes = []
        inicio_parte = 0

        while inicio_parte < len(texto):

            fim_parte = inicio_parte
            ultima_posicao_valida = inicio_parte

            while fim_parte < len(texto):

                teste = texto[inicio_parte:fim_parte + 1]

                if metricas.horizontalAdvance(teste) <= largura_maxima:
                    ultima_posicao_valida = fim_parte + 1
                    fim_parte += 1
                else:
                    break

            if fim_parte >= len(texto):

                partes.append((
                    texto[inicio_parte:],
                    inicio_parte
                ))

                break

            if ultima_posicao_valida == inicio_parte:

                partes.append((
                    texto[inicio_parte:inicio_parte + 1],
                    inicio_parte
                ))

                inicio_parte += 1
                continue

            corte = texto.rfind(
                " ",
                inicio_parte,
                ultima_posicao_valida
            )

            if corte >= inicio_parte:

                partes.append((
                    texto[inicio_parte:corte],
                    inicio_parte
                ))

                inicio_parte = corte + 1

                while (
                    inicio_parte < len(texto)
                    and texto[inicio_parte] == " "
                ):
                    inicio_parte += 1

            else:

                partes.append((
                    texto[inicio_parte:ultima_posicao_valida],
                    inicio_parte
                ))

                inicio_parte = ultima_posicao_valida

        altura_texto = metricas.height()
        total_altura = len(partes) * altura_texto

        y_inicial = (
            y
            - (total_altura / 2)
            + metricas.ascent()
        )

        for numero_parte, (parte, inicio) in enumerate(partes):

            y_parte = int(
                y_inicial + numero_parte * altura_texto
            )

            largura = metricas.horizontalAdvance(parte)

            x = (self.width() - largura) / 2

            if indice != 1:

                painter.setPen(QColor("#555566"))

                painter.drawText(
                    int(x),
                    y_parte,
                    parte
                )

                continue

            for posicao_local, caractere in enumerate(parte):

                posicao_real = inicio + posicao_local

                resultado = (
                    progresso[posicao_real]
                    if posicao_real < len(progresso)
                    else None
                )

                if resultado is True:
                    cor = QColor("#34D399")

                elif resultado is False:
                    cor = QColor("#F87171")

                else:
                    cor = QColor("#FFFFFF")

                painter.setPen(cor)

                painter.drawText(
                    int(x),
                    y_parte,
                    caractere
                )

                x += metricas.horizontalAdvance(caractere)

    # ======================================
    # ATUALIZAR PROGRESSO
    # ======================================

    def atualizar_progresso(self, progresso):

        self.progresso = list(progresso)
        self.update()

    # ======================================
    # ANIMAÇÃO DAS LINHAS
    # ======================================

    def avancar_linhas(self, novas_linhas, novo_progresso):

        if self.animacao.state() == QPropertyAnimation.State.Running:
            return

        self.novas_linhas = list(novas_linhas)
        self.novo_progresso = list(novo_progresso)

        self._deslocamento = 0

        self.animacao.stop()

        self.animacao.setStartValue(0.0)
        self.animacao.setEndValue(float(self.altura_linha))

        self.animacao.start()

    def finalizar_animacao(self):

        if self.novas_linhas is not None:

            self.linhas = self.novas_linhas
            self.progresso = self.novo_progresso

        self.novas_linhas = None
        self.novo_progresso = None

        self._deslocamento = 0

        self.update()


# ==========================================
# JOGO PRINCIPAL
# ==========================================

class TypeBeat(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("TypeBeat")
        self.setMinimumSize(1100, 700)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # ÁUDIO

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()

        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(0.5)

        # DADOS

        self.letras = []
        self.indice_atual = -1
        self.indice_caractere = 0
        self.progresso = []

        # PONTUAÇÃO

        self.pontuacao = 0
        self.acertos = 0
        self.erros = 0
        self.combo = 0
        self.multiplicador = 1

        # BUSCA AUTOMÁTICA

        self.busca_thread = None
        self.caminho_musica = None

        # CONTAGEM REGRESSIVA

        self.contagem = 0

        self.timer_contagem = QTimer(self)
        self.timer_contagem.setInterval(1000)

        self.timer_contagem.timeout.connect(
            self.atualizar_contagem
        )

        self.jogo_iniciado = False

        # INTERFACE

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(15)

        titulo = QLabel("TYPEBEAT")

        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titulo.setStyleSheet("""
            color: #A78BFA;
            font-size: 48px;
            font-weight: bold;
        """)

        layout.addWidget(titulo)

        self.nome_musica = QLabel(
            "Nenhuma música selecionada"
        )

        self.nome_musica.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.nome_musica.setStyleSheet("""
            color: white;
            font-size: 16px;
        """)

        layout.addWidget(self.nome_musica)

        self.painel_status = QLabel()

        self.painel_status.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.painel_status.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            padding: 10px;
        """)

        layout.addWidget(self.painel_status)

        self.atualizar_painel()

        # STATUS DA BUSCA E CONTAGEM

        self.status_busca = QLabel("")

        self.status_busca.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.status_busca.setWordWrap(True)

        self.status_busca.setStyleSheet("""
            color: #A78BFA;
            font-size: 22px;
            font-weight: bold;
            padding: 10px;
        """)

        layout.addWidget(self.status_busca)

        # LETRAS

        self.area_letras = AreaLetras()

        layout.addWidget(self.area_letras)

        # BOTÕES

        botao_musica = QPushButton("ESCOLHER MÚSICA")
        botao_letra = QPushButton("CARREGAR LETRA LRC")
        botao_pausar = QPushButton("PAUSAR")
        botao_continuar = QPushButton("CONTINUAR")

        botoes = [
            botao_musica,
            botao_letra,
            botao_pausar,
            botao_continuar
        ]

        for botao in botoes:

            botao.setFixedSize(280, 45)

            botao.setFocusPolicy(
                Qt.FocusPolicy.NoFocus
            )

            botao.setStyleSheet("""
                QPushButton {
                    background-color: #7C3AED;
                    color: white;
                    font-size: 15px;
                    font-weight: bold;
                    border: none;
                    border-radius: 10px;
                }

                QPushButton:hover {
                    background-color: #A78BFA;
                }

                QPushButton:pressed {
                    background-color: #5B21B6;
                }
            """)

            layout.addWidget(
                botao,
                alignment=Qt.AlignmentFlag.AlignCenter
            )

        botao_musica.clicked.connect(
            self.selecionar_musica
        )

        botao_letra.clicked.connect(
            self.selecionar_letra
        )

        botao_pausar.clicked.connect(
            self.player.pause
        )

        botao_continuar.clicked.connect(
            self.continuar_jogo
        )

        # TEMPORIZADOR DE SINCRONIZAÇÃO

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.atualizar_letra
        )

        self.timer.start(50)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #11111B;
            }
        """)

    # ======================================
    # ESCOLHER MÚSICA E BUSCAR LETRA
    # ======================================

    def selecionar_musica(self):

        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Escolha sua música",
            "",
            "Áudio (*.mp3 *.wav *.flac *.ogg)"
        )

        if not arquivo:
            return

        if self.busca_thread and self.busca_thread.isRunning():

            self.status_busca.setText(
                "Aguarde a busca da música anterior terminar."
            )

            return

        self.timer_contagem.stop()
        self.jogo_iniciado = False

        self.caminho_musica = arquivo

        self.player.stop()

        self.player.setSource(
            QUrl.fromLocalFile(arquivo)
        )

        self.nome_musica.setText(
            os.path.basename(arquivo)
        )

        self.status_busca.setText(
            "Procurando letra sincronizada na LRCLIB..."
        )

        self.letras = []

        self.indice_atual = -1
        self.indice_caractere = 0
        self.progresso = []

        self.area_letras.animacao.stop()

        self.area_letras.linhas = [
            "",
            "Buscando letra...",
            ""
        ]

        self.area_letras.progresso = []

        self.area_letras.update()

        self.busca_thread = BuscaLetraThread(arquivo)

        self.busca_thread.sucesso.connect(
            self.letra_encontrada
        )

        self.busca_thread.falha.connect(
            self.erro_busca
        )

        self.busca_thread.start()

        self.setFocus()

    # ======================================
    # LETRA ENCONTRADA
    # ======================================

    def letra_encontrada(self, texto_lrc, nome_musica):

        arquivo_temporario = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".lrc",
            delete=False
        )

        try:

            arquivo_temporario.write(texto_lrc)
            arquivo_temporario.close()

            self.letras = carregar_letras(
                arquivo_temporario.name
            )

        finally:

            if os.path.exists(arquivo_temporario.name):
                os.remove(arquivo_temporario.name)

        if not self.letras:

            self.erro_busca(
                "A LRCLIB retornou uma letra sem linhas sincronizadas."
            )

            return

        self.nome_musica.setText(nome_musica)

        self.resetar_jogo()

        self.indice_atual = 0
        self.indice_caractere = 0

        self.progresso = [
            None
        ] * len(
            self.letras[0]["texto"]
        )

        self.mostrar_tres_linhas(0)

        self.player.pause()
        self.player.setPosition(0)

        self.iniciar_contagem()

        self.setFocus()

    # ======================================
    # CONTAGEM REGRESSIVA
    # ======================================

    def iniciar_contagem(self):

        self.timer_contagem.stop()

        self.player.pause()
        self.player.setPosition(0)

        self.contagem = 3
        self.jogo_iniciado = False

        self.status_busca.setText(
            "LETRA ENCONTRADA!\nPrepare-se: 3"
        )

        self.timer_contagem.start()

    def atualizar_contagem(self):

        self.contagem -= 1

        if self.contagem > 0:

            self.status_busca.setText(
                f"LETRA ENCONTRADA!\nPrepare-se: {self.contagem}"
            )

        else:

            self.timer_contagem.stop()

            self.status_busca.setText("GO!")

            self.jogo_iniciado = True

            self.player.setPosition(0)
            self.player.play()

            self.setFocus()

            QTimer.singleShot(
                700,
                lambda: self.status_busca.setText("")
            )

    # ======================================
    # ERRO NA BUSCA
    # ======================================

    def erro_busca(self, mensagem):

        self.status_busca.setText(
            "Não foi possível encontrar a letra automaticamente.\n"
            + mensagem
            + "\nVocê pode carregar um arquivo LRC manualmente."
        )

        self.setFocus()

    # ======================================
    # CARREGAR LRC MANUALMENTE
    # ======================================

    def selecionar_letra(self):

        arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Escolha a letra sincronizada",
            "assets",
            "Arquivos LRC (*.lrc)"
        )

        if arquivo:

            self.letras = carregar_letras(arquivo)

            if not self.letras:

                self.status_busca.setText(
                    "Esse arquivo LRC não possui linhas válidas."
                )

                return

            self.resetar_jogo()

            self.indice_atual = 0
            self.indice_caractere = 0

            self.progresso = [
                None
            ] * len(
                self.letras[0]["texto"]
            )

            self.mostrar_tres_linhas(0)

            self.status_busca.setText(
                "LETRA CARREGADA!"
            )

            if self.caminho_musica:
                self.iniciar_contagem()

            self.setFocus()

    # ======================================
    # MOSTRAR TRÊS LINHAS
    # ======================================

    def mostrar_tres_linhas(self, indice):

        anterior = ""

        if indice > 0:
            anterior = self.letras[indice - 1]["texto"]

        atual = self.letras[indice]["texto"]

        proxima = ""

        if indice + 1 < len(self.letras):
            proxima = self.letras[indice + 1]["texto"]

        self.area_letras.animacao.stop()

        self.area_letras.linhas = [
            anterior,
            atual,
            proxima
        ]

        self.area_letras.progresso = list(
            self.progresso
        )

        self.area_letras.update()

    # ======================================
    # CONTINUAR JOGO
    # ======================================

    def continuar_jogo(self):

        if self.letras and not self.jogo_iniciado:
            self.iniciar_contagem()
        else:
            self.player.play()

    # ======================================
    # RESETAR JOGO
    # ======================================

    def resetar_jogo(self):

        self.timer_contagem.stop()
        self.jogo_iniciado = False

        self.pontuacao = 0
        self.acertos = 0
        self.erros = 0
        self.combo = 0
        self.multiplicador = 1

        self.indice_atual = -1
        self.indice_caractere = 0

        self.progresso = []

        self.area_letras.animacao.stop()

        self.area_letras.linhas = [
            "",
            "Aguardando a música...",
            ""
        ]

        self.area_letras.progresso = []

        self.area_letras.update()

        self.atualizar_painel()

    # ======================================
    # DIGITAÇÃO
    # ======================================

    def keyPressEvent(self, event):

        if not self.jogo_iniciado:
            return

        if not self.letras or self.indice_atual < 0:
            return

        if self.area_letras.animacao.state() == QPropertyAnimation.State.Running:
            return

        texto_digitado = event.text()

        if len(texto_digitado) != 1:
            return

        # Aceitar somente letras.
        # Espaços, números e pontuação são ignorados.

        if not texto_digitado.isalpha():
            return

        linha = self.letras[
            self.indice_atual
        ]["texto"]

        # Pular automaticamente caracteres que não são letras.

        while self.indice_caractere < len(linha):

            caractere = linha[self.indice_caractere]

            if not caractere.isalpha():

                self.progresso[self.indice_caractere] = True
                self.indice_caractere += 1

            else:
                break

        if self.indice_caractere >= len(linha):
            return

        caractere_esperado = linha[
            self.indice_caractere
        ]

        acertou = (
            texto_digitado.casefold()
            == caractere_esperado.casefold()
        )

        self.progresso[
            self.indice_caractere
        ] = acertou

        if acertou:

            self.acertos += 1
            self.combo += 1

            if self.combo >= 100:
                self.multiplicador = 5

            elif self.combo >= 50:
                self.multiplicador = 4

            elif self.combo >= 25:
                self.multiplicador = 3

            elif self.combo >= 10:
                self.multiplicador = 2

            else:
                self.multiplicador = 1

            self.pontuacao += (
                100 * self.multiplicador
            )

        else:

            self.erros += 1
            self.combo = 0
            self.multiplicador = 1

        self.indice_caractere += 1

        # Pular os próximos espaços e sinais automaticamente.

        while self.indice_caractere < len(linha):

            caractere = linha[self.indice_caractere]

            if not caractere.isalpha():

                self.progresso[self.indice_caractere] = True
                self.indice_caractere += 1

            else:
                break

        self.area_letras.atualizar_progresso(
            self.progresso
        )

        self.atualizar_painel()

    # ======================================
    # SINCRONIZAÇÃO COM A MÚSICA
    # ======================================

    def atualizar_letra(self):

        if not self.letras or not self.jogo_iniciado:
            return

        if self.area_letras.animacao.state() == QPropertyAnimation.State.Running:
            return

        tempo = self.player.position()

        indice = encontrar_linha_atual(
            self.letras,
            tempo
        )

        if indice == self.indice_atual:
            return

        if indice < 0:
            return

        self.indice_atual = indice
        self.indice_caractere = 0

        self.progresso = [
            None
        ] * len(
            self.letras[indice]["texto"]
        )

        anterior = ""

        if indice > 0:
            anterior = self.letras[indice - 1]["texto"]

        atual = self.letras[indice]["texto"]

        proxima = ""

        if indice + 1 < len(self.letras):
            proxima = self.letras[indice + 1]["texto"]

        novas_linhas = [
            anterior,
            atual,
            proxima
        ]

        if not self.area_letras.linhas or (
            self.area_letras.linhas[1] == "Aguardando a música..."
            or self.area_letras.linhas[1] == "Aguardando o início da letra..."
            or self.area_letras.linhas[1] == "Buscando letra..."
        ):

            self.area_letras.linhas = novas_linhas

            self.area_letras.progresso = list(
                self.progresso
            )

            self.area_letras.update()

        else:

            self.area_letras.avancar_linhas(
                novas_linhas,
                self.progresso
            )

    # ======================================
    # PAINEL DE PONTUAÇÃO
    # ======================================

    def atualizar_painel(self):

        total = self.acertos + self.erros

        if total > 0:
            precisao = (self.acertos / total) * 100
        else:
            precisao = 0

        self.painel_status.setText(
            f"PONTOS: {self.pontuacao}     "
            f"COMBO: {self.combo}     "
            f"x{self.multiplicador}\n\n"
            f"ACERTOS: {self.acertos}     "
            f"ERROS: {self.erros}     "
            f"PRECISÃO: {precisao:.1f}%"
        )


# ==========================================
# INICIAR JOGO
# ==========================================

if __name__ == "__main__":

    app = QApplication(sys.argv)

    janela = TypeBeat()

    janela.show()

    sys.exit(app.exec())
