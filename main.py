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


#  ESTADOS DO AFD — Cada estado é uma função isolada

def estado_inicial(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q0 do AFD — ponto de entrada para cada ciclo de reconhecimento."""
    tamanho = len(fonte)

    # Consumir espaços e quebras de linha
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

    # Verificar fim da entrada (EOF)
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

    # Dígito -> transição para estado_inteiro
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

    # Caractere não reconhecido -> erro léxico
    raise ErroLexico(f"Caractere inesperado: '{ch}' (ord={ord(ch)})", linha, coluna)


def estado_inteiro(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q1 — Leitura da parte inteira de um número. Aplica Maximal Munch."""
    inicio_pos = pos
    inicio_col = coluna
    tamanho    = len(fonte)

    while pos < tamanho and _eh_digito(fonte[pos]):
        pos    += 1
        coluna += 1

    # Transição para parte fracionária?
    if pos < tamanho and fonte[pos] == '.':
        return estado_ponto(fonte, pos, linha, coluna, inicio_pos, inicio_col)

    lexema = fonte[inicio_pos:pos]
    token  = Token(TIPO_NUMERO, lexema, linha, inicio_col)
    return (token, pos, linha, coluna)


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
    token  = Token(TIPO_NUMERO, lexema, linha, inicio_col)
    return (token, pos, linha, coluna)


def estado_divisao(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q4 — Aplica MAXIMAL MUNCH para operador de divisão (/ vs //)."""
    inicio_col = coluna
    pos    += 1
    coluna += 1

    if pos < len(fonte) and fonte[pos] == '/':
        token = Token(TIPO_OPERADOR, "//", linha, inicio_col)
        return (token, pos + 1, linha, coluna + 1)

    token = Token(TIPO_OPERADOR, "/", linha, inicio_col)
    return (token, pos, linha, coluna)


def estado_identificador(fonte: str, pos: int, linha: int, coluna: int):
    """Estado q5 — Leitura de identificadores (sequências de letras maiúsculas)."""
    inicio_pos = pos
    inicio_col = coluna
    tamanho    = len(fonte)

    while pos < tamanho and _eh_letra_maiuscula(fonte[pos]):
        pos    += 1
        coluna += 1

    lexema = fonte[inicio_pos:pos]
    token  = Token(TIPO_IDENTIFICADOR, lexema, linha, inicio_col)
    return (token, pos, linha, coluna)


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


#  FUNÇÕES DE I/O

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


# 
#
#  Pilha RPN no ARM:
#    NUMERO  -> ldr r0, =label / vldr.f64 d0, [r0] / vpush {d0}
#    OP +    -> vpop {d1} / vpop {d0} / vadd.f64 d0, d0, d1 / vpush {d0}
#    OP -    -> vpop {d1} / vpop {d0} / vsub.f64 d0, d0, d1 / vpush {d0}
#    OP *    -> vpop {d1} / vpop {d0} / vmul.f64 d0, d0, d1 / vpush {d0}
#    OP /    -> vpop {d1} / vpop {d0} / vdiv.f64 d0, d0, d1 / vpush {d0}
#
#  Ordem dos operandos (CRÍTICO para - e /):
#    RPN (A B -) -> push A, push B
#    vpop {d1} = B (topo)    vpop {d0} = A (segundo)
#    vsub.f64 d0, d0, d1  ->  d0 = A - B

# Mapeamento: operador RPN -> instrução VFP 64-bit
_MAPA_INSTRUCOES_VFP = {
    '+': ('vadd.f64', 'soma'),
    '-': ('vsub.f64', 'subtração'),
    '*': ('vmul.f64', 'multiplicação'),
    '/': ('vdiv.f64', 'divisão real'),
}

# Operadores
_OPERADORES_COMMIT3 = {
    '//': 'divisão inteira',
    '%':  'resto / módulo',
    '^':  'potência',
}


def _agrupar_por_linha(tokens: list) -> list:
    """Agrupa tokens por número de linha da fonte original."""
    grupos  = {}
    ordem   = []

    for i, tok in enumerate(tokens):
        if tok.tipo == TIPO_EOF:
            continue
        if tok.linha not in grupos:
            grupos[tok.linha] = []
            ordem.append(tok.linha)
        grupos[tok.linha].append((i, tok))

    return [(nl, grupos[nl]) for nl in ordem]


def _gerar_secao_data(asm: list, constantes: list, num_linhas: int):
    """Gera a seção .data (constantes IEEE 754 double + array de resultados)."""
    asm.append("@ Seção de dados (.data)")
    asm.append("@ Constantes IEEE 754 double-precision (64 bits)")
    asm.append(".section .data")
    asm.append("    .align 3")
    asm.append("")

    # Constantes numéricas
    asm.append("@ --- Constantes numéricas (geradas pelo compilador) ---")
    for rotulo, valor in constantes:
        asm.append(f"{rotulo}:")
        asm.append(f"    .double {valor}")
    asm.append("")

    # Array de resultados (infraestrutura para RES)
    asm.append("@ --- Array de resultados por linha (infraestrutura para RES) ---")
    asm.append("resultados:")
    asm.append(f"    .space {num_linhas * 8}    @ {num_linhas} linhas * 8 bytes")
    asm.append("")
    asm.append("num_resultados:")
    asm.append("    .word 0")
    asm.append("")


def _emitir_push_numero(asm: list, rotulo: str, valor_display: str):
    """Emite instruções ARM para carregar um double da .data e empilhar."""
    asm.append(f"    @ Push {valor_display}")
    asm.append(f"    ldr r0, ={rotulo}")
    asm.append(f"    vldr.f64 d0, [r0]")
    asm.append(f"    vpush {{d0}}")


def _emitir_operador_basico(asm: list, operador: str):
    """Emite instruções ARM para operação aritmética básica (+,-,*,/)."""
    instrucao, nome = _MAPA_INSTRUCOES_VFP[operador]

    asm.append(f"    @ Operador '{operador}' ({nome})")
    asm.append(f"    vpop {{d1}}              @ d1 = operando do topo (B)")
    asm.append(f"    vpop {{d0}}              @ d0 = segundo operando (A)")
    asm.append(f"    {instrucao} d0, d0, d1  @ d0 = A {operador} B")
    asm.append(f"    vpush {{d0}}             @ empilha resultado")


def _emitir_operador_pendente(asm: list, operador: str):
    """Emite placeholder para operadores do(//, %, ^). Mantém pilha balanceada."""
    nome = _OPERADORES_COMMIT3.get(operador, operador)

    asm.append(f"    @ TODO []: Operador '{operador}' ({nome})")
    asm.append(f"    vpop {{d1}}              @ d1 = operando do topo (B)")
    asm.append(f"    vpop {{d0}}              @ d0 = segundo operando (A)")
    asm.append(f"    @ Placeholder: mantém d0 inalterado (resultado incorreto)")
    asm.append(f"    vpush {{d0}}             @ empilha placeholder")


def _emitir_armazenar_resultado(asm: list, num_linha: int, idx_slot: int):
    """Emite instruções para salvar o resultado da expressão no array 'resultados'."""
    asm.append(f"    @ --- Armazenar resultado da linha {num_linha} (slot {idx_slot}) ---")
    asm.append(f"    vpop {{d0}}              @ d0 = resultado da expressão")
    asm.append(f"    ldr r1, =resultados")

    if idx_slot > 0:
        offset = idx_slot * 8
        asm.append(f"    add r1, r1, #{offset}      @ offset = slot {idx_slot} * 8 bytes")

    asm.append(f"    vstr.f64 d0, [r1]       @ salvar double no array")
    asm.append(f"    @ Incrementar contador")
    asm.append(f"    ldr r2, =num_resultados")
    asm.append(f"    ldr r3, [r2]")
    asm.append(f"    add r3, r3, #1")
    asm.append(f"    str r3, [r2]")


def _gerar_secao_text(asm: list, grupos: list, rotulos: dict):
    """Gera a seção .text do Assembly ARM com o código executável."""
    asm.append("@ Seção de código (.text)")
    asm.append("@ Pilha RPN simulada via SP (vpush/vpop de registradores VFP)")
    asm.append(".section .text")
    asm.append(".global _start")
    asm.append("")
    asm.append("_start:")

    linhas_completas   = 0
    linhas_pendentes   = 0

    for idx_slot, (num_linha, grupo) in enumerate(grupos):
        tem_pendente = False
        stack_depth  = 0

        # Reconstruir expressão original para comentário
        expressao_display = ""
        for _, tok in grupo:
            expressao_display += tok.valor + " "
        expressao_display = expressao_display.strip()

        asm.append(f"")
        asm.append(f"@ --- Linha {num_linha}: {expressao_display} ---")

        # Percorrer tokens da linha
        for idx_tok, tok in grupo:

            # Parênteses: ignorar (RPN puro usa pilha)
            if tok.tipo == TIPO_ABRE_PAREN or tok.tipo == TIPO_FECHA_PAREN:
                continue

            # Número: carregar da .data e empilhar
            elif tok.tipo == TIPO_NUMERO:
                rotulo = rotulos[idx_tok]
                _emitir_push_numero(asm, rotulo, tok.valor)
                stack_depth += 1

            # Operador: desempilhar, operar, empilhar resultado
            elif tok.tipo == TIPO_OPERADOR:
                if tok.valor in _MAPA_INSTRUCOES_VFP:
                    _emitir_operador_basico(asm, tok.valor)
                else:
                    _emitir_operador_pendente(asm, tok.valor)
                    tem_pendente = True
                stack_depth -= 1

            # Identificador: TODO para  (MEM, RES, variáveis)
            elif tok.tipo == TIPO_IDENTIFICADOR:
                tem_pendente = True
                asm.append(f"    @ TODO : Identificador '{tok.valor}'")
                asm.append(f"    @ (variável, MEM ou RES — nenhuma instrução emitida)")

        # Fim da linha: armazenar resultado se pilha está correta
        if stack_depth == 1 and not tem_pendente:
            _emitir_armazenar_resultado(asm, num_linha, idx_slot)
            linhas_completas += 1
        elif stack_depth == 1 and tem_pendente:
            asm.append(f"    @ [AVISO] Linha {num_linha}: resultado é placeholder (ops pendentes)")
            _emitir_armazenar_resultado(asm, num_linha, idx_slot)
            linhas_pendentes += 1
        else:
            asm.append(f"    @ [AVISO] Linha {num_linha}: resultado não armazenado")
            asm.append(f"    @         (pilha desbalanceada: depth={stack_depth}, "
                       f"identificadores pendentes)")
            linhas_pendentes += 1

    # Finalização do programa
    asm.append(f"")
    asm.append(f"@ Fim do programa")
    asm.append(f"@ Resumo: {linhas_completas} completas, {linhas_pendentes} pendentes ")
    asm.append(f"@ Resultados no array 'resultados' na .data")
    asm.append(f"")
    asm.append(f"_halt:")
    asm.append(f"    b _halt                  @ Loop infinito (inspecionar no debugger)")


def gerarAssembly(tokens: list) -> str:
    """Função principal: traduz tokens em Assembly ARMv7."""
    asm = []

    # Cabeçalho
    asm.append("@ Código Assembly ARMv7 — Gerado pelo Compilador RPN")
    asm.append("@ Alvo: CPUlator ARMv7 DE1-SoC (v16.1)")
    asm.append("@ Padrão: IEEE 754 double-precision (64-bit)")
    asm.append("@ Instruções: VFP (vldr, vadd, vsub, vmul, vdiv .f64)")
    asm.append("")

    # Fase 1: Coletar constantes numéricas e gerar rótulos
    rotulos    = {}
    constantes = []
    idx_const  = 0

    for i, tok in enumerate(tokens):
        if tok.tipo == TIPO_NUMERO:
            rotulo = f"const_{idx_const}"
            rotulos[i] = rotulo

            # Garantir formato double: "100" -> "100.0"
            valor = tok.valor
            if '.' not in valor:
                valor = valor + ".0"

            constantes.append((rotulo, valor))
            idx_const += 1

    # Fase 2: Agrupar tokens por linha
    grupos     = _agrupar_por_linha(tokens)
    num_linhas = len(grupos)

    # Fase 3: Gerar seção .data
    _gerar_secao_data(asm, constantes, num_linhas)

    # Fase 4: Gerar seção .text
    _gerar_secao_text(asm, grupos, rotulos)

    return '\n'.join(asm) + '\n'


def salvarAssembly(codigo_asm: str, caminho: str):
    """Salva o código Assembly gerado em um arquivo .s."""
    with open(caminho, 'w', encoding='utf-8') as f:
        f.write(codigo_asm)


def exibirResumoAssembly(codigo_asm: str, caminho: str):
    """Exibe um resumo do Assembly gerado no console."""
    linhas_asm    = codigo_asm.split('\n')
    total_linhas  = len(linhas_asm)
    linhas_codigo = 0
    linhas_coment = 0
    linhas_vazio  = 0
    count_vpush   = 0
    count_vpop    = 0
    count_vadd    = 0
    count_vsub    = 0
    count_vmul    = 0
    count_vdiv    = 0
    count_todo    = 0

    for l in linhas_asm:
        stripped = l.strip()
        if not stripped:
            linhas_vazio += 1
        elif stripped[0] == '@':
            linhas_coment += 1
            if 'TODO' in stripped:
                count_todo += 1
        else:
            linhas_codigo += 1
            if 'vpush' in stripped:
                count_vpush += 1
            if 'vpop' in stripped:
                count_vpop += 1
            if 'vadd.f64' in stripped:
                count_vadd += 1
            if 'vsub.f64' in stripped:
                count_vsub += 1
            if 'vmul.f64' in stripped:
                count_vmul += 1
            if 'vdiv.f64' in stripped:
                count_vdiv += 1

    print()
    print("=" * 65)
    print("  RESUMO DO ASSEMBLY GERADO")
    print("=" * 65)
    print(f"  Arquivo:      {caminho}")
    print(f"  Total linhas: {total_linhas} ({linhas_codigo} código, "
          f"{linhas_coment} comentários, {linhas_vazio} vazias)")
    print(f"  Instruções VFP:")
    print(f"    vpush:     {count_vpush:>4}  (empilhamentos)")
    print(f"    vpop:      {count_vpop:>4}  (desempilhamentos)")
    print(f"    vadd.f64:  {count_vadd:>4}  (somas)")
    print(f"    vsub.f64:  {count_vsub:>4}  (subtrações)")
    print(f"    vmul.f64:  {count_vmul:>4}  (multiplicações)")
    print(f"    vdiv.f64:  {count_vdiv:>4}  (divisões)")
    if count_todo > 0:
        print(f"  Pendências:  {count_todo} marcadores TODO ")
    print("=" * 65)
    print()


#  PONTO DE ENTRADA — Interface de Linha de Comando (CLI)

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
        # Etapa 1: Leitura
        print(f"\n[1/4] Lendo arquivo: {caminho_entrada}")
        fonte = lerArquivo(caminho_entrada)
        print(f"      {len(fonte)} caracteres lidos, "
              f"{fonte.count(chr(10)) + 1} linha(s) detectada(s).")

        # Etapa 2: Análise Léxica (AFD)
        print("[2/4] Executando análise léxica (AFD)...")
        tokens = parseExpressao(fonte)
        n_tokens = len(tokens) - 1
        print(f"      {n_tokens} tokens reconhecidos + EOF.")

        # Etapa 3: Salvar tokens
        print(f"[3/4] Salvando tokens:")
        print(f"      → {caminho_json}")
        print(f"      → {caminho_txt}")
        salvarTokens(tokens, caminho_json, caminho_txt)

        # Etapa 4: Gerar Assembly ARMv7
        print(f"[4/4] Gerando Assembly ARMv7 (IEEE 754 / VFP 64-bit)...")
        codigo_asm = gerarAssembly(tokens)
        salvarAssembly(codigo_asm, caminho_asm)
        print(f"      → {caminho_asm}")

        # Exibir resumos
        exibirTokens(tokens)
        exibirResumoAssembly(codigo_asm, caminho_asm)

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