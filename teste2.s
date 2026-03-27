@ Código Assembly ARMv7 — Gerado pelo Compilador RPN
@ Alvo: CPUlator ARMv7 DE1-SoC (v16.1)
@ Padrão: IEEE 754 double-precision (64-bit)
@ Instruções: VFP (vldr, vadd, vsub, vmul, vdiv .f64)

@ Seção de dados (.data)
@ Constantes IEEE 754 double-precision (64 bits)
.section .data
    .align 3

@ --- Constantes numéricas (geradas pelo compilador) ---
const_0:
    .double 15.0
const_1:
    .double 5.0
const_2:
    .double 2.0
const_3:
    .double 3.0
const_4:
    .double 2.0
const_5:
    .double 1.0
const_6:
    .double 1.0
const_7:
    .double 3.0
const_8:
    .double 2.0
const_9:
    .double 25.0
const_10:
    .double 5.0
const_11:
    .double 2.0
const_12:
    .double 7.0
const_13:
    .double 2.0
const_14:
    .double 4.0
const_15:
    .double 1.0

@ --- Array de resultados por linha (infraestrutura para RES) ---
resultados:
    .space 80    @ 10 linhas * 8 bytes

num_resultados:
    .word 0

@ Seção de código (.text)
@ Pilha RPN simulada via SP (vpush/vpop de registradores VFP)
.section .text
.global _start

_start:

@ --- Linha 1: ( 15.0 VARA ) ---
    @ Push 15.0
    ldr r0, =const_0
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO : Identificador 'VARA'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ [AVISO] Linha 1: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 1 (slot 0) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 2: ( 5.0 VARB ) ---
    @ Push 5.0
    ldr r0, =const_1
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO : Identificador 'VARB'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ [AVISO] Linha 2: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 2 (slot 1) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #8      @ offset = slot 1 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 3: ( ( ( VARA ) ( VARB ) + ) 2.0 / ) ---
    @ TODO : Identificador 'VARA'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ TODO : Identificador 'VARB'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ Operador '+' (soma)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    vadd.f64 d0, d0, d1  @ d0 = A + B
    vpush {d0}             @ empilha resultado
    @ Push 2.0
    ldr r0, =const_2
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '/' (divisão real)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    vdiv.f64 d0, d0, d1  @ d0 = A / B
    vpush {d0}             @ empilha resultado
    @ [AVISO] Linha 3: resultado não armazenado
    @         (pilha desbalanceada: depth=-1, identificadores pendentes)

@ --- Linha 4: ( 3.0 2.0 ^ ) ---
    @ Push 3.0
    ldr r0, =const_3
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 2.0
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO []: Operador '^' (potência)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    @ Placeholder: mantém d0 inalterado (resultado incorreto)
    vpush {d0}             @ empilha placeholder
    @ [AVISO] Linha 4: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 4 (slot 3) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #24      @ offset = slot 3 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 5: ( 1 RES ) ---
    @ Push 1
    ldr r0, =const_5
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO : Identificador 'RES'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ [AVISO] Linha 5: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 5 (slot 4) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #32      @ offset = slot 4 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 6: ( ( ( 1 RES ) 3.0 * ) 2.0 % ) ---
    @ Push 1
    ldr r0, =const_6
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO : Identificador 'RES'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ Push 3.0
    ldr r0, =const_7
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '*' (multiplicação)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    vmul.f64 d0, d0, d1  @ d0 = A * B
    vpush {d0}             @ empilha resultado
    @ Push 2.0
    ldr r0, =const_8
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO []: Operador '%' (resto / módulo)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    @ Placeholder: mantém d0 inalterado (resultado incorreto)
    vpush {d0}             @ empilha placeholder
    @ [AVISO] Linha 6: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 6 (slot 5) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #40      @ offset = slot 5 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 7: ( ( 25.0 5.0 // ) 2.0 + ) ---
    @ Push 25.0
    ldr r0, =const_9
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 5.0
    ldr r0, =const_10
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO []: Operador '//' (divisão inteira)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    @ Placeholder: mantém d0 inalterado (resultado incorreto)
    vpush {d0}             @ empilha placeholder
    @ Push 2.0
    ldr r0, =const_11
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '+' (soma)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    vadd.f64 d0, d0, d1  @ d0 = A + B
    vpush {d0}             @ empilha resultado
    @ [AVISO] Linha 7: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 7 (slot 6) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #48      @ offset = slot 6 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 8: ( 7.0 VARC ) ---
    @ Push 7.0
    ldr r0, =const_12
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO : Identificador 'VARC'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ [AVISO] Linha 8: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 8 (slot 7) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #56      @ offset = slot 7 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 9: ( ( ( VARA ) ( VARC ) * ) ( ( VARB ) 2.0 ^ ) - ) ---
    @ TODO : Identificador 'VARA'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ TODO : Identificador 'VARC'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ Operador '*' (multiplicação)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    vmul.f64 d0, d0, d1  @ d0 = A * B
    vpush {d0}             @ empilha resultado
    @ TODO : Identificador 'VARB'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ Push 2.0
    ldr r0, =const_13
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO []: Operador '^' (potência)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    @ Placeholder: mantém d0 inalterado (resultado incorreto)
    vpush {d0}             @ empilha placeholder
    @ Operador '-' (subtração)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    vsub.f64 d0, d0, d1  @ d0 = A - B
    vpush {d0}             @ empilha resultado
    @ [AVISO] Linha 9: resultado não armazenado
    @         (pilha desbalanceada: depth=-2, identificadores pendentes)

@ --- Linha 10: ( ( 4 RES ) ( 1 RES ) + ) ---
    @ Push 4
    ldr r0, =const_14
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO : Identificador 'RES'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ Push 1
    ldr r0, =const_15
    vldr.f64 d0, [r0]
    vpush {d0}
    @ TODO : Identificador 'RES'
    @ (variável, MEM ou RES — nenhuma instrução emitida)
    @ Operador '+' (soma)
    vpop {d1}              @ d1 = operando do topo (B)
    vpop {d0}              @ d0 = segundo operando (A)
    vadd.f64 d0, d0, d1  @ d0 = A + B
    vpush {d0}             @ empilha resultado
    @ [AVISO] Linha 10: resultado é placeholder (ops pendentes)
    @ --- Armazenar resultado da linha 10 (slot 9) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #72      @ offset = slot 9 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    @ Incrementar contador
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ Fim do programa
@ Resumo: 0 completas, 10 pendentes 
@ Resultados no array 'resultados' na .data

_halt:
    b _halt                  @ Loop infinito (inspecionar no debugger)
