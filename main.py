#!/usr/bin/env python3
"""
==============================================================================
  Compilador RPN → ARMv7 Assembly (IEEE 754 / VFP)
==============================================================================
"""

import sys
import json
import os

#  CONSTANTES — Tipos de Token

TIPO_NUMERO        = "NUMERO"
TIPO_OPERADOR      = "OPERADOR"
TIPO_ABRE_PAREN    = "ABRE_PAREN"
TIPO_FECHA_PAREN   = "FECHA_PAREN"
TIPO_IDENTIFICADOR = "IDENTIFICADOR"
TIPO_EOF           = "EOF"


#  CLASSE TOKEN

class Token:
    """
    Representa uma unidade léxica (token) extraída da entrada.
    Atributos:
        tipo   (str): Categoria do token (NUMERO, OPERADOR, etc.)
        valor  (str): Lexema original extraído da fonte
        linha  (int): Linha onde o token inicia (base 1)
        coluna (int): Coluna onde o token inicia (base 1)
    """

    __slots__ = ('tipo', 'valor', 'linha', 'coluna')

    def __init__(self, tipo: str, valor: str, linha: int, coluna: int):
        self.tipo   = tipo
        self.valor  = valor
        self.linha  = linha
        self.coluna = coluna

    # -- Serialização --------------------------------------------------------

    def to_dict(self) -> dict:
        """Converte o token para dicionário (serialização JSON)."""
        return {
            "tipo":   self.tipo,
            "valor":  self.valor,
            "linha":  self.linha,
            "coluna": self.coluna
        }

    def __repr__(self) -> str:
        return f"Token({self.tipo}, '{self.valor}', L{self.linha}:C{self.coluna})"



#  CLASSE DE ERRO LÉXICO

class ErroLexico(Exception):
    """Exceção lançada quando o AFD encontra entrada inválida."""

    def __init__(self, mensagem: str, linha: int, coluna: int):
        self.linha  = linha
        self.coluna = coluna
        super().__init__(f"Erro Léxico [L{linha}:C{coluna}]: {mensagem}")


#  FUNÇÕES AUXILIARES (sem regex / comparações diretas de caractere)

def _eh_digito(ch: str) -> bool:
    """Retorna True se ch ∈ [0-9]. """
    return '0' <= ch <= '9'


def _eh_letra_maiuscula(ch: str) -> bool:
    """Retorna True se ch ∈ [A-Z]. """
    return 'A' <= ch <= 'Z'


def _eh_espaco(ch: str) -> bool:
    """Retorna True se ch é espaço, tab, ou carriage return"""
    return ch == ' ' or ch == '\t' or ch == '\r'

def estado_inicial(fonte: str, pos: int, linha: int, coluna: int):
    """
    Estado q0 do AFD — ponto de entrada para cada ciclo de reconhecimento.
    """
    tamanho = len(fonte)

    # ── Consumir espaços e quebras de linha 
    while pos < tamanho:
        ch = fonte[pos]
        if ch == '\n':
            linha  += 1
            coluna  = 1
            pos    += 1
        elif _eh_espaco(ch):
            coluna += 1
            pos    += 1
        else:
            break

    # ── Verificar fim da entrada (EOF) 
    if pos >= tamanho:
        return (Token(TIPO_EOF, "", linha, coluna), pos, linha, coluna)

    ch = fonte[pos]


    # Parêntese de abertura
    if ch == '(':
        token = Token(TIPO_ABRE_PAREN, "(", linha, coluna)
        return (token, pos + 1, linha, coluna + 1)

    # Parêntese de fechamento
    if ch == ')':
        token = Token(TIPO_FECHA_PAREN, ")", linha, coluna)
        return (token, pos + 1, linha, coluna + 1)

    # Dígito → transição para estado_inteiro
    if _eh_digito(ch):
        return estado_inteiro(fonte, pos, linha, coluna)

    # Operadores de caractere único: + - * % ^
    if ch == '+' or ch == '-' or ch == '*' or ch == '%' or ch == '^':
        token = Token(TIPO_OPERADOR, ch, linha, coluna)
        return (token, pos + 1, linha, coluna + 1)

    # Barra -> transição para estado_divisao (Maximal Munch: / vs //)
    if ch == '/':
        return estado_divisao(fonte, pos, linha, coluna)

    # Letra maiúscula -> transição para estado_identificador
    if _eh_letra_maiuscula(ch):
        return estado_identificador(fonte, pos, linha, coluna)

    #  Caractere não reconhecido -> erro léxico 
    raise ErroLexico(f"Caractere inesperado: '{ch}' (ord={ord(ch)})", linha, coluna)


def estado_inteiro(fonte: str, pos: int, linha: int, coluna: int):
    """
    Estado q1 — Leitura da parte inteira de um número.
    Aplica Maximal Munch: consome o máximo de dígitos possível.
    """
    inicio_pos = pos
    inicio_col = coluna
    tamanho    = len(fonte)

    # Loop: consumir dígitos consecutivos
    while pos < tamanho and _eh_digito(fonte[pos]):
        pos    += 1
        coluna += 1

    # Transição para parte fracionária?
    if pos < tamanho and fonte[pos] == '.':
        return estado_ponto(fonte, pos, linha, coluna, inicio_pos, inicio_col)

    # Estado de aceitação: emitir número inteiro
    lexema = fonte[inicio_pos:pos]
    token  = Token(TIPO_NUMERO, lexema, linha, inicio_col)
    return (token, pos, linha, coluna)


def estado_ponto(fonte: str, pos: int, linha: int, coluna: int,
                 inicio_pos: int, inicio_col: int):
    """
    Estado q2 — Ponto decimal encontrado após parte inteira.
    """
    pos    += 1    # consumir o '.'
    coluna += 1

    if pos >= len(fonte) or not _eh_digito(fonte[pos]):
        raise ErroLexico(
            "Esperado dígito após ponto decimal (ex: '3.0', não '3.')",
            linha, coluna
        )

    return estado_real(fonte, pos, linha, coluna, inicio_pos, inicio_col)


def estado_real(fonte: str, pos: int, linha: int, coluna: int,
                inicio_pos: int, inicio_col: int):
    """
    Estado q3 — Leitura da parte fracionária de um número real.
    """
    tamanho = len(fonte)

    # Loop: consumir dígitos da parte fracionária
    while pos < tamanho and _eh_digito(fonte[pos]):
        pos    += 1
        coluna += 1

    # Estado de aceitação: emitir número real
    lexema = fonte[inicio_pos:pos]
    token  = Token(TIPO_NUMERO, lexema, linha, inicio_col)
    return (token, pos, linha, coluna)


def estado_divisao(fonte: str, pos: int, linha: int, coluna: int):
    """
    Estado q4 — Aplica MAXIMAL MUNCH para operador de divisão.
    """
    inicio_col = coluna
    pos    += 1    # consumir primeiro '/'
    coluna += 1

    # Lookahead: verificar segundo '/'
    if pos < len(fonte) and fonte[pos] == '/':
        token = Token(TIPO_OPERADOR, "//", linha, inicio_col)
        return (token, pos + 1, linha, coluna + 1)

    # Token simples: apenas '/'
    token = Token(TIPO_OPERADOR, "/", linha, inicio_col)
    return (token, pos, linha, coluna)


def estado_identificador(fonte: str, pos: int, linha: int, coluna: int):
    """
    Estado q5 — Leitura de identificadores (sequências de letras maiúsculas).
    """
    inicio_pos = pos
    inicio_col = coluna
    tamanho    = len(fonte)

    # Loop: consumir letras maiúsculas consecutivas
    while pos < tamanho and _eh_letra_maiuscula(fonte[pos]):
        pos    += 1
        coluna += 1

    # Estado de aceitação: emitir identificador
    lexema = fonte[inicio_pos:pos]
    token  = Token(TIPO_IDENTIFICADOR, lexema, linha, inicio_col)
    return (token, pos, linha, coluna)


#  ANALISADOR LÉXICO — Orquestrador do AFD

def parseExpressao(fonte: str) -> list:
    """
    Executa a análise léxica completa sobre a string de entrada.
    """
    tokens = []
    pos    = 0
    linha  = 1
    coluna = 1

    while True:
        resultado = estado_inicial(fonte, pos, linha, coluna)
        token, pos, linha, coluna = resultado
        tokens.append(token)

        if token.tipo == TIPO_EOF:
            break

    return tokens


#  FUNÇÕES DE I/O

def lerArquivo(caminho: str) -> str:
    """
    Lê o arquivo de entrada contendo expressões RPN.
    """
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: '{caminho}'")

    with open(caminho, 'r', encoding='utf-8') as f:
        conteudo = f.read()

    if not conteudo.strip():
        raise ValueError(f"Arquivo vazio: '{caminho}'")

    return conteudo


def salvarTokens(tokens: list, caminho_json: str, caminho_txt: str):
    """
    Persiste o fluxo de tokens em dois formatos:
    """
    # ── Salvar JSON ──────────────────────────────────────────────────
    dados_json = [t.to_dict() for t in tokens]
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados_json, f, indent=2, ensure_ascii=False)

    # ── Salvar TXT tabular ───────────────────────────────────────────
    with open(caminho_txt, 'w', encoding='utf-8') as f:
        f.write("=" * 65 + "\n")
        f.write("  FLUXO DE TOKENS — Analisador Léxico (AFD)\n")
        f.write("=" * 65 + "\n\n")

        f.write(f"{'#':<6}{'TIPO':<20}{'LEXEMA':<15}{'POSICAO':<12}\n")
        f.write("-" * 53 + "\n")

        for i, t in enumerate(tokens):
            pos_str = f"L{t.linha}:C{t.coluna}"
            valor_display = t.valor if t.valor else "(vazio)"
            f.write(f"{i:<6}{t.tipo:<20}{valor_display:<15}{pos_str:<12}\n")

        f.write("-" * 53 + "\n")
        f.write(f"Total de tokens: {len(tokens)}\n")


def exibirTokens(tokens: list):
    """Exibe o fluxo de tokens no console de forma formatada."""
    print()
    print("=" * 65)
    print("  FLUXO DE TOKENS — Analisador Léxico (AFD)")
    print("=" * 65)
    print()
    print(f"{'#':<6}{'TIPO':<20}{'LEXEMA':<15}{'POSICAO':<12}")
    print("-" * 53)

    for i, t in enumerate(tokens):
        pos_str = f"L{t.linha}:C{t.coluna}"
        valor_display = t.valor if t.valor else "(vazio)"
        print(f"{i:<6}{t.tipo:<20}{valor_display:<15}{pos_str:<12}")

    print("-" * 53)
    print(f"Total de tokens: {len(tokens)}")
    print()


#  PONTO DE ENTRADA — Interface de Linha de Comando (CLI)

def main():
    """
    Função principal.
    """
    # ── Validar argumentos CLI ───────────────────────────────────────
    if len(sys.argv) < 2:
        print("╔══════════════════════════════════════════════════════╗")
        print("║  Compilador RPN → ARMv7 Assembly                    ║")
        print("║  Uso: python compilador_rpn.py <arquivo_entrada.txt>║")
        print("║  Ex:  python compilador_rpn.py expressoes.txt       ║")
        print("╚══════════════════════════════════════════════════════╝")
        sys.exit(1)

    caminho_entrada = sys.argv[1]

    # Derivar nomes dos arquivos de saída a partir do nome de entrada
    nome_base   = os.path.splitext(os.path.basename(caminho_entrada))[0]
    dir_saida   = os.path.dirname(caminho_entrada) or "."
    caminho_json = os.path.join(dir_saida, f"{nome_base}_tokens.json")
    caminho_txt  = os.path.join(dir_saida, f"{nome_base}_tokens.txt")

    try:
        # Etapa 1: Leitura 
        print(f"\n[1/3] Lendo arquivo: {caminho_entrada}")
        fonte = lerArquivo(caminho_entrada)
        print(f"      {len(fonte)} caracteres lidos, "
              f"{fonte.count(chr(10)) + 1} linha(s) detectada(s).")

        # Etapa 2: Análise Léxica (AFD) 
        print("[2/3] Executando análise léxica (AFD)...")
        tokens = parseExpressao(fonte)
        n_tokens = len(tokens) - 1   # descontar EOF
        print(f"      {n_tokens} tokens reconhecidos + EOF.")

        #Etapa 3: Saída 
        print(f"[3/3] Salvando tokens:")
        print(f"      → {caminho_json}")
        print(f"      → {caminho_txt}")
        salvarTokens(tokens, caminho_json, caminho_txt)
        exibirTokens(tokens)

    except ErroLexico as e:
        print(f"\n✖ {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as e:
        print(f"\n✖ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\n✖ {e}", file=sys.stderr)
        sys.exit(1)


# ── Execução 
if __name__ == "__main__":
    main()