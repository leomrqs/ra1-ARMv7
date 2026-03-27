#!/usr/bin/env python3
"""
==============================================================================
  Compilador RPN → ARMv7 Assembly (IEEE 754 / VFP)
  Analisador Léxico (AFD) + Parser Recursivo + Gerador de Código
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
    """Retorna True se ch ∈ [0-9]."""
    return '0' <= ch <= '9'

def _eh_letra_maiuscula(ch: str) -> bool:
    """Retorna True se ch ∈ [A-Z]."""
    return 'A' <= ch <= 'Z'

def _eh_espaco(ch: str) -> bool:
    """Retorna True se ch é espaço, tab, ou carriage return."""
    return ch == ' ' or ch == '\t' or ch == '\r'


# ============================================================================
#  ESTADOS DO AFD — Cada estado é uma função isolada
# ============================================================================

def estado_inicial(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q0 do AFD — ponto de entrada para cada ciclo de reconhecimento."""
    tamanho = len(fonte)

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

    if pos >= tamanho:
        return (Token(TIPO_EOF, "", linha, coluna), pos, linha, coluna)

    ch = fonte[pos]

    if ch == '(':
        return (Token(TIPO_ABRE_PAREN, "(", linha, coluna), pos + 1, linha, coluna + 1)
    if ch == ')':
        return (Token(TIPO_FECHA_PAREN, ")", linha, coluna), pos + 1, linha, coluna + 1)
    if _eh_digito(ch):
        return estado_inteiro(fonte, pos, linha, coluna)
    if ch == '+' or ch == '-' or ch == '*' or ch == '%' or ch == '^':
        return (Token(TIPO_OPERADOR, ch, linha, coluna), pos + 1, linha, coluna + 1)
    if ch == '/':
        return estado_divisao(fonte, pos, linha, coluna)
    if _eh_letra_maiuscula(ch):
        return estado_identificador(fonte, pos, linha, coluna)

    raise ErroLexico(f"Caractere inesperado: '{ch}' (ord={ord(ch)})", linha, coluna)


def estado_inteiro(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q1 — Leitura da parte inteira de um número. Aplica Maximal Munch."""
    inicio_pos = pos
    inicio_col = coluna
    tamanho    = len(fonte)

    while pos < tamanho and _eh_digito(fonte[pos]):
        pos    += 1
        coluna += 1

    if pos < tamanho and fonte[pos] == '.':
        return estado_ponto(fonte, pos, linha, coluna, inicio_pos, inicio_col)

    lexema = fonte[inicio_pos:pos]
    return (Token(TIPO_NUMERO, lexema, linha, inicio_col), pos, linha, coluna)


def estado_ponto(fonte: str, pos: int, linha: int, coluna: int,
                 inicio_pos: int, inicio_col: int):
    """Estado q2 — Ponto decimal encontrado após parte inteira."""
    pos    += 1
    coluna += 1
    if pos >= len(fonte) or not _eh_digito(fonte[pos]):
        raise ErroLexico(
            "Esperado dígito após ponto decimal (ex: '3.0', não '3.')",
            linha, coluna
        )
    return estado_real(fonte, pos, linha, coluna, inicio_pos, inicio_col)


def estado_real(fonte: str, pos: int, linha: int, coluna: int,
                inicio_pos: int, inicio_col: int):
    """Estado q3 — Leitura da parte fracionária de um número real."""
    tamanho = len(fonte)
    while pos < tamanho and _eh_digito(fonte[pos]):
        pos    += 1
        coluna += 1
    lexema = fonte[inicio_pos:pos]
    return (Token(TIPO_NUMERO, lexema, linha, inicio_col), pos, linha, coluna)


def estado_divisao(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q4 — Aplica MAXIMAL MUNCH para operador de divisão (/ vs //)."""
    inicio_col = coluna
    pos    += 1
    coluna += 1
    if pos < len(fonte) and fonte[pos] == '/':
        return (Token(TIPO_OPERADOR, "//", linha, inicio_col), pos + 1, linha, coluna + 1)
    return (Token(TIPO_OPERADOR, "/", linha, inicio_col), pos, linha, coluna)


def estado_identificador(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q5 — Leitura de identificadores (sequências de letras maiúsculas)."""
    inicio_pos = pos
    inicio_col = coluna
    tamanho    = len(fonte)
    while pos < tamanho and _eh_letra_maiuscula(fonte[pos]):
        pos    += 1
        coluna += 1
    lexema = fonte[inicio_pos:pos]
    return (Token(TIPO_IDENTIFICADOR, lexema, linha, inicio_col), pos, linha, coluna)


#  ANALISADOR LÉXICO — Orquestrador do AFD

def parseExpressao(fonte: str) -> list:
    """Executa a análise léxica completa sobre a string de entrada."""
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


# ============================================================================
#  FUNÇÕES DE I/O
# ============================================================================

def lerArquivo(caminho: str) -> str:
    """Lê o arquivo de entrada contendo expressões RPN."""
    if not os.path.isfile(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: '{caminho}'")
    with open(caminho, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    if not conteudo.strip():
        raise ValueError(f"Arquivo vazio: '{caminho}'")
    return conteudo


def salvarTokens(tokens: list, caminho_json: str, caminho_txt: str):
    """Persiste o fluxo de tokens em JSON e TXT tabular."""
    dados_json = [t.to_dict() for t in tokens]
    with open(caminho_json, 'w', encoding='utf-8') as f:
        json.dump(dados_json, f, indent=2, ensure_ascii=False)

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


# ============================================================================
#  PARSER RECURSIVO — Converte tokens planos em AST
# ============================================================================
#  Padrões: (A B op) → OP_BIN | (V NOME) → ESCREVER_VAR
#           (NOME)   → LER_VAR | (N RES)  → LER_RES

def _parsear_nodo(tokens, pos):
    """Parse recursivo de um nodo da expressão RPN parentesizada."""
    tok = tokens[pos]

    if tok.tipo != TIPO_ABRE_PAREN:
        return tok, pos + 1

    pos += 1  # pular '('
    filhos = []
    while tokens[pos].tipo != TIPO_FECHA_PAREN:
        if tokens[pos].tipo == TIPO_ABRE_PAREN:
            filho, pos = _parsear_nodo(tokens, pos)
            filhos.append(filho)
        else:
            filhos.append(tokens[pos])
            pos += 1
    pos += 1  # pular ')'

    return _classificar_nodo(filhos), pos


def _classificar_nodo(filhos):
    """Classifica um nodo da AST baseado no padrão dos filhos."""
    n = len(filhos)

    # (VARNAME) → leitura de variável
    if n == 1:
        f = filhos[0]
        if isinstance(f, Token) and f.tipo == TIPO_IDENTIFICADOR and f.valor != 'RES':
            return {'tipo': 'LER_VAR', 'nome': f.valor}
        return f

    # 2 filhos: (V VARNAME) ou (N RES)
    if n == 2:
        primeiro, segundo = filhos
        if isinstance(segundo, Token) and segundo.tipo == TIPO_IDENTIFICADOR:
            if segundo.valor == 'RES':
                return {'tipo': 'LER_RES', 'n_valor': primeiro}
            else:
                return {'tipo': 'ESCREVER_VAR', 'nome': segundo.valor, 'expr': primeiro}

    # 3 filhos: (A B op) → operação binária
    if n == 3:
        esq, dir_, op = filhos
        if isinstance(op, Token) and op.tipo == TIPO_OPERADOR:
            return {'tipo': 'OP_BIN', 'esq': esq, 'dir': dir_, 'op': op.valor}

    return {'tipo': 'DESCONHECIDO', 'filhos': filhos}


# ============================================================================
#  GERADOR DE ASSEMBLY ARMv7 (IEEE 754 / VFP 64-bit)
# ============================================================================
#  Pilha RPN no ARM:
#    NUMERO  -> ldr r0, =label / vldr.f64 d0, [r0] / vpush {d0}
#    OP +,-  -> vpop {d1}(B) / vpop {d0}(A) / vOP d0,d0,d1 / vpush {d0}
#  Ordem: vpop d1=B(topo), vpop d0=A(segundo) -> d0 = A op B

_MAPA_INSTRUCOES_VFP = {
    '+': ('vadd.f64', 'soma'),
    '-': ('vsub.f64', 'subtração'),
    '*': ('vmul.f64', 'multiplicação'),
    '/': ('vdiv.f64', 'divisão real'),
}


def _coletar_constantes(tokens):
    """Coleta todos os tokens NUMERO e gera rótulos para a seção .data."""
    rotulos    = {}
    constantes = []
    idx        = 0
    for tok in tokens:
        if tok.tipo == TIPO_NUMERO:
            chave = (tok.linha, tok.coluna)
            rotulo = f"const_{idx}"
            rotulos[chave] = rotulo
            valor = tok.valor if '.' in tok.valor else tok.valor + ".0"
            constantes.append((rotulo, valor))
            idx += 1
    return rotulos, constantes


def _coletar_variaveis(tokens):
    """Coleta nomes de variáveis únicas (identificadores exceto RES)."""
    variaveis = []
    visto     = set()
    for tok in tokens:
        if tok.tipo == TIPO_IDENTIFICADOR and tok.valor != 'RES':
            if tok.valor not in visto:
                variaveis.append(tok.valor)
                visto.add(tok.valor)
    return variaveis


def _agrupar_por_linha(tokens):
    """Agrupa tokens por número de linha da fonte original."""
    grupos = {}
    ordem  = []
    for tok in tokens:
        if tok.tipo == TIPO_EOF:
            continue
        if tok.linha not in grupos:
            grupos[tok.linha] = []
            ordem.append(tok.linha)
        grupos[tok.linha].append(tok)
    return [(nl, grupos[nl]) for nl in ordem]


# --- Geração da seção .data ------------------------------------------------

def _gerar_secao_data(asm, constantes, variaveis, num_linhas):
    """Gera a seção .data (constantes + variáveis + array de resultados)."""
    asm.append("@ Seção de dados (.data)")
    asm.append(".section .data")
    asm.append("    .align 3")
    asm.append("")

    asm.append("@ --- Constantes numéricas (IEEE 754 double) ---")
    for rotulo, valor in constantes:
        asm.append(f"{rotulo}:")
        asm.append(f"    .double {valor}")
    asm.append("")

    asm.append("@ --- Constante utilitária ---")
    asm.append("const_um:")
    asm.append("    .double 1.0")
    asm.append("")

    if variaveis:
        asm.append("@ --- Variáveis de memória (inicializadas em 0.0) ---")
        for nome in variaveis:
            asm.append(f"var_{nome}:")
            asm.append(f"    .double 0.0")
        asm.append("")

    asm.append("@ --- Array de resultados por linha (para RES) ---")
    asm.append("resultados:")
    asm.append(f"    .space {num_linhas * 8}    @ {num_linhas} linhas * 8 bytes")
    asm.append("")
    asm.append("num_resultados:")
    asm.append("    .word 0")
    asm.append("")


# --- Emissão de instruções --------------------------------------------------

def _emitir_push_numero(asm, rotulo, valor_display):
    """Carrega um double da .data e empilha."""
    asm.append(f"    @ Push {valor_display}")
    asm.append(f"    ldr r0, ={rotulo}")
    asm.append(f"    vldr.f64 d0, [r0]")
    asm.append(f"    vpush {{d0}}")


def _emitir_operador_basico(asm, operador):
    """Operação aritmética básica (+, -, *, /)."""
    instrucao, nome = _MAPA_INSTRUCOES_VFP[operador]
    asm.append(f"    @ Operador '{operador}' ({nome})")
    asm.append(f"    vpop {{d1}}              @ d1 = B (topo)")
    asm.append(f"    vpop {{d0}}              @ d0 = A (segundo)")
    asm.append(f"    {instrucao} d0, d0, d1  @ d0 = A {operador} B")
    asm.append(f"    vpush {{d0}}")


def _emitir_divisao_inteira(asm):
    """Divisão inteira (//) via truncamento: double -> int32 -> double."""
    asm.append(f"    @ Operador '//' (divisão inteira)")
    asm.append(f"    vpop {{d1}}              @ d1 = B")
    asm.append(f"    vpop {{d0}}              @ d0 = A")
    asm.append(f"    vdiv.f64 d0, d0, d1     @ d0 = A / B")
    asm.append(f"    vcvt.s32.f64 s4, d0     @ s4 = truncar para int32")
    asm.append(f"    vcvt.f64.s32 d0, s4     @ d0 = de volta para double")
    asm.append(f"    vpush {{d0}}")


def _emitir_resto(asm):
    """Resto/módulo (%) via fmod: A - trunc(A/B) * B."""
    asm.append(f"    @ Operador '%' (resto via fmod)")
    asm.append(f"    vpop {{d1}}              @ d1 = B")
    asm.append(f"    vpop {{d0}}              @ d0 = A")
    asm.append(f"    vdiv.f64 d2, d0, d1     @ d2 = A / B")
    asm.append(f"    vcvt.s32.f64 s6, d2     @ s6 = trunc(A/B) como int32")
    asm.append(f"    vcvt.f64.s32 d2, s6     @ d2 = trunc(A/B) como double")
    asm.append(f"    vmul.f64 d2, d2, d1     @ d2 = trunc(A/B) * B")
    asm.append(f"    vsub.f64 d0, d0, d2     @ d0 = A - trunc(A/B)*B = resto")
    asm.append(f"    vpush {{d0}}")


def _emitir_potencia(asm, ctx):
    """Potência (^) via loop de multiplicações. Expoente inteiro positivo."""
    idx = ctx['label_counter']
    ctx['label_counter'] = idx + 1

    asm.append(f"    @ Operador '^' (potência por loop)")
    asm.append(f"    vpop {{d1}}              @ d1 = B (expoente)")
    asm.append(f"    vpop {{d0}}              @ d0 = A (base)")
    asm.append(f"    vcvt.s32.f64 s4, d1     @ converter expoente para int32")
    asm.append(f"    vmov r4, s4              @ r4 = expoente inteiro")
    asm.append(f"    vmov.f64 d2, d0          @ d2 = base (backup)")
    asm.append(f"    cmp r4, #0")
    asm.append(f"    beq _pow_zero_{idx}")
    asm.append(f"    cmp r4, #1")
    asm.append(f"    beq _pow_fim_{idx}")
    asm.append(f"    sub r4, r4, #1")
    asm.append(f"_pow_loop_{idx}:")
    asm.append(f"    vmul.f64 d0, d0, d2     @ d0 *= base")
    asm.append(f"    subs r4, r4, #1")
    asm.append(f"    bne _pow_loop_{idx}")
    asm.append(f"    b _pow_fim_{idx}")
    asm.append(f"_pow_zero_{idx}:")
    asm.append(f"    ldr r0, =const_um")
    asm.append(f"    vldr.f64 d0, [r0]       @ d0 = 1.0")
    asm.append(f"_pow_fim_{idx}:")
    asm.append(f"    vpush {{d0}}")


def _emitir_armazenar_resultado(asm, num_linha, idx_slot):
    """Salva o resultado no array 'resultados' e incrementa contador."""
    asm.append(f"    @ --- Armazenar resultado da linha {num_linha} (slot {idx_slot}) ---")
    asm.append(f"    vpop {{d0}}              @ d0 = resultado da expressão")
    asm.append(f"    ldr r1, =resultados")
    if idx_slot > 0:
        offset = idx_slot * 8
        asm.append(f"    add r1, r1, #{offset}      @ offset = slot {idx_slot} * 8 bytes")
    asm.append(f"    vstr.f64 d0, [r1]       @ salvar double no array")
    asm.append(f"    ldr r2, =num_resultados")
    asm.append(f"    ldr r3, [r2]")
    asm.append(f"    add r3, r3, #1")
    asm.append(f"    str r3, [r2]")


# --- Caminhamento da AST para geração de código ----------------------------

def _gerar_asm_nodo(asm, nodo, ctx):
    """Gera assembly recursivamente percorrendo a AST."""

    # Folha: Token literal (número)
    if isinstance(nodo, Token):
        if nodo.tipo == TIPO_NUMERO:
            chave = (nodo.linha, nodo.coluna)
            rotulo = ctx['rotulos'][chave]
            _emitir_push_numero(asm, rotulo, nodo.valor)
        return

    tipo = nodo['tipo']

    # Leitura de variável: (VARNAME) -> vldr + vpush
    if tipo == 'LER_VAR':
        nome = nodo['nome']
        asm.append(f"    @ Ler variável {nome}")
        asm.append(f"    ldr r0, =var_{nome}")
        asm.append(f"    vldr.f64 d0, [r0]")
        asm.append(f"    vpush {{d0}}")

    # Escrita de variável: (V VARNAME) -> avaliar V, salvar, manter na pilha
    elif tipo == 'ESCREVER_VAR':
        _gerar_asm_nodo(asm, nodo['expr'], ctx)
        nome = nodo['nome']
        asm.append(f"    @ Salvar em variável {nome}")
        asm.append(f"    vpop {{d0}}")
        asm.append(f"    ldr r1, =var_{nome}")
        asm.append(f"    vstr.f64 d0, [r1]")
        asm.append(f"    vpush {{d0}}             @ manter na pilha como resultado")

    # Leitura de histórico: (N RES) -> carregar resultado de N linhas atrás
    elif tipo == 'LER_RES':
        n_valor = nodo['n_valor']
        if isinstance(n_valor, Token) and n_valor.tipo == TIPO_NUMERO:
            n = int(n_valor.valor)
            idx_alvo = ctx['idx_linha'] - n
            offset = idx_alvo * 8
            asm.append(f"    @ RES: resultado de {n} linha(s) atrás (slot {idx_alvo})")
            asm.append(f"    ldr r0, =resultados")
            if offset > 0:
                asm.append(f"    add r0, r0, #{offset}")
            asm.append(f"    vldr.f64 d0, [r0]")
            asm.append(f"    vpush {{d0}}")

    # Operação binária: (A B op)
    elif tipo == 'OP_BIN':
        _gerar_asm_nodo(asm, nodo['esq'], ctx)
        _gerar_asm_nodo(asm, nodo['dir'], ctx)
        op = nodo['op']
        if op in _MAPA_INSTRUCOES_VFP:
            _emitir_operador_basico(asm, op)
        elif op == '//':
            _emitir_divisao_inteira(asm)
        elif op == '%':
            _emitir_resto(asm)
        elif op == '^':
            _emitir_potencia(asm, ctx)


# --- Geração da seção .text ------------------------------------------------

def _gerar_secao_text(asm, grupos, rotulos):
    """Gera a seção .text processando cada linha via parser + AST walker."""
    asm.append("@ Seção de código (.text)")
    asm.append(".section .text")
    asm.append(".global _start")
    asm.append("")
    asm.append("_start:")

    ctx = {
        'rotulos':       rotulos,
        'label_counter': 0,
    }

    for idx_slot, (num_linha, tokens_linha) in enumerate(grupos):
        ctx['idx_linha'] = idx_slot

        expressao_display = " ".join(tok.valor for tok in tokens_linha)
        asm.append(f"")
        asm.append(f"@ --- Linha {num_linha}: {expressao_display} ---")

        nodo, _ = _parsear_nodo(tokens_linha, 0)
        _gerar_asm_nodo(asm, nodo, ctx)
        _emitir_armazenar_resultado(asm, num_linha, idx_slot)

    asm.append(f"")
    asm.append(f"@ --- Fim do programa ---")
    asm.append(f"@ Resultados no array 'resultados' na .data")
    asm.append(f"")
    asm.append(f"_halt:")
    asm.append(f"    b _halt                  @ Loop infinito (inspecionar no debugger)")


# --- Orquestrador principal ------------------------------------------------

def gerarAssembly(tokens):
    """Traduz o fluxo de tokens em código Assembly ARMv7 completo."""
    asm = []

    asm.append("@ Código Assembly ARMv7 — Gerado pelo Compilador RPN")
    asm.append("@ Alvo: CPUlator ARMv7 DE1-SoC (v16.1)")
    asm.append("@ Padrão: IEEE 754 double-precision (64-bit)")
    asm.append("@ Instruções: VFP (vldr, vadd, vsub, vmul, vdiv, vcvt .f64)")
    asm.append("")

    rotulos, constantes = _coletar_constantes(tokens)
    variaveis           = _coletar_variaveis(tokens)
    grupos              = _agrupar_por_linha(tokens)
    num_linhas          = len(grupos)

    _gerar_secao_data(asm, constantes, variaveis, num_linhas)
    _gerar_secao_text(asm, grupos, rotulos)

    return '\n'.join(asm) + '\n'


def salvarAssembly(codigo_asm, caminho):
    """Salva o código Assembly gerado em um arquivo .s."""
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(codigo_asm)


def exibirResumoAssembly(codigo_asm, caminho):
    """Exibe um resumo do Assembly gerado no console."""
    linhas_asm    = codigo_asm.split('\n')
    total_linhas  = len(linhas_asm)
    linhas_codigo = 0
    linhas_coment = 0
    linhas_vazio  = 0
    contadores    = {
        'vpush': 0, 'vpop': 0,
        'vadd.f64': 0, 'vsub.f64': 0, 'vmul.f64': 0, 'vdiv.f64': 0,
        'vcvt': 0, 'vstr.f64': 0, 'vldr.f64': 0,
    }

    for l in linhas_asm:
        stripped = l.strip()
        if not stripped:
            linhas_vazio += 1
        elif stripped[0] == '@':
            linhas_coment += 1
        else:
            linhas_codigo += 1
            for chave in contadores:
                if chave in stripped:
                    contadores[chave] += 1

    print()
    print("=" * 65)
    print("  RESUMO DO ASSEMBLY GERADO")
    print("=" * 65)
    print(f"  Arquivo:      {caminho}")
    print(f"  Total linhas: {total_linhas} ({linhas_codigo} código, "
          f"{linhas_coment} comentários, {linhas_vazio} vazias)")
    print(f"  Instruções VFP:")
    print(f"    vpush:     {contadores['vpush']:>4}  (empilhamentos)")
    print(f"    vpop:      {contadores['vpop']:>4}  (desempilhamentos)")
    print(f"    vldr.f64:  {contadores['vldr.f64']:>4}  (carregamentos)")
    print(f"    vstr.f64:  {contadores['vstr.f64']:>4}  (armazenamentos)")
    print(f"    vadd.f64:  {contadores['vadd.f64']:>4}  (somas)")
    print(f"    vsub.f64:  {contadores['vsub.f64']:>4}  (subtrações)")
    print(f"    vmul.f64:  {contadores['vmul.f64']:>4}  (multiplicações)")
    print(f"    vdiv.f64:  {contadores['vdiv.f64']:>4}  (divisões)")
    print(f"    vcvt:      {contadores['vcvt']:>4}  (conversões int/float)")
    print("=" * 65)
    print()


#  PONTO DE ENTRADA

def main():
    """Função principal."""
    if len(sys.argv) < 2:
        print("╔══════════════════════════════════════════════════════╗")
        print("║  Compilador RPN → ARMv7 Assembly                    ║")
        print("║  Uso: python compilador_rpn.py <arquivo_entrada.txt>║")
        print("║  Ex:  python compilador_rpn.py teste1.txt           ║")
        print("╚══════════════════════════════════════════════════════╝")
        sys.exit(1)

    caminho_entrada = sys.argv[1]
    nome_base    = os.path.splitext(os.path.basename(caminho_entrada))[0]
    caminho_json = f"{nome_base}_tokens.json"
    caminho_txt  = f"{nome_base}_tokens.txt"
    caminho_asm  = f"{nome_base}.s"

    try:
        print(f"\n[1/4] Lendo arquivo: {caminho_entrada}")
        fonte = lerArquivo(caminho_entrada)
        print(f"      {len(fonte)} caracteres lidos, "
              f"{fonte.count(chr(10)) + 1} linha(s) detectada(s).")

        print("[2/4] Executando análise léxica (AFD)...")
        tokens = parseExpressao(fonte)
        n_tokens = len(tokens) - 1
        print(f"      {n_tokens} tokens reconhecidos + EOF.")

        print(f"[3/4] Salvando tokens:")
        print(f"      → {caminho_json}")
        print(f"      → {caminho_txt}")
        salvarTokens(tokens, caminho_json, caminho_txt)

        print(f"[4/4] Gerando Assembly ARMv7 (IEEE 754 / VFP 64-bit)...")
        codigo_asm = gerarAssembly(tokens)
        salvarAssembly(codigo_asm, caminho_asm)
        print(f"      → {caminho_asm}")

        exibirTokens(tokens)
        exibirResumoAssembly(codigo_asm, caminho_asm)

        print("Compilação concluída com sucesso.")
        print(f"    Copie '{caminho_asm}' para o CPUlator ARMv7 DE1-SoC")
        print(f"    e execute para verificar os resultados no debugger.\n")

    except ErroLexico as e:
        print(f"\n✖ {e}", file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as e:
        print(f"\n✖ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"\n✖ {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()