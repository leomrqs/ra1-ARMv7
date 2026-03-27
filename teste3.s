@ Código Assembly ARMv7 — Gerado pelo Compilador RPN
@ Alvo: CPUlator ARMv7 DE1-SoC (v16.1)
@ Padrão: IEEE 754 double-precision (64-bit)
@ Instruções: VFP (vldr, vadd, vsub, vmul, vdiv, vcvt .f64)

@ Seção de dados (.data)
.section .data
    .align 3

@ --- Constantes numéricas (IEEE 754 double) ---
const_0:
    .double 100.0
const_1:
    .double 3.0
const_2:
    .double 100.0
const_3:
    .double 3.0
const_4:
    .double 2.0
const_5:
    .double 8.0
const_6:
    .double 100.0
const_7:
    .double 3.0
const_8:
    .double 2.0
const_9:
    .double 8.0
const_10:
    .double 2.0
const_11:
    .double 45.5
const_12:
    .double 2.5
const_13:
    .double 10.0
const_14:
    .double 2.0
const_15:
    .double 2.0
const_16:
    .double 0.5
const_17:
    .double 2.0
const_18:
    .double 3.0
const_19:
    .double 5.0
const_20:
    .double 1.0
const_21:
    .double 2.0
const_22:
    .double 3.0

@ --- Constante utilitária ---
const_um:
    .double 1.0

@ --- Variáveis de memória (inicializadas em 0.0) ---
var_TEMPORARIO:
    .double 0.0

@ --- Array de resultados por linha (para RES) ---
resultados:
    .space 80    @ 10 linhas * 8 bytes

num_resultados:
    .word 0

@ Seção de código (.text)
.section .text
.global _start

_start:

@ --- Linha 1: ( 100.0 3.0 // ) ---
    @ Push 100.0
    ldr r0, =const_0
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 3.0
    ldr r0, =const_1
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '//' (divisão inteira)
    vpop {d1}              @ d1 = B
    vpop {d0}              @ d0 = A
    vdiv.f64 d0, d0, d1     @ d0 = A / B
    vcvt.s32.f64 s4, d0     @ s4 = truncar para int32
    vcvt.f64.s32 d0, s4     @ d0 = de volta para double
    vpush {d0}
    @ --- Armazenar resultado da linha 1 (slot 0) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 2: ( 100.0 3.0 % ) ---
    @ Push 100.0
    ldr r0, =const_2
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 3.0
    ldr r0, =const_3
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '%' (resto via fmod)
    vpop {d1}              @ d1 = B
    vpop {d0}              @ d0 = A
    vdiv.f64 d2, d0, d1     @ d2 = A / B
    vcvt.s32.f64 s6, d2     @ s6 = trunc(A/B) como int32
    vcvt.f64.s32 d2, s6     @ d2 = trunc(A/B) como double
    vmul.f64 d2, d2, d1     @ d2 = trunc(A/B) * B
    vsub.f64 d0, d0, d2     @ d0 = A - trunc(A/B)*B = resto
    vpush {d0}
    @ --- Armazenar resultado da linha 2 (slot 1) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #8      @ offset = slot 1 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 3: ( 2.0 8.0 ^ ) ---
    @ Push 2.0
    ldr r0, =const_4
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 8.0
    ldr r0, =const_5
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '^' (potência por loop)
    vpop {d1}              @ d1 = B (expoente)
    vpop {d0}              @ d0 = A (base)
    vcvt.s32.f64 s4, d1     @ converter expoente para int32
    vmov r4, s4              @ r4 = expoente inteiro
    vmov.f64 d2, d0          @ d2 = base (backup)
    cmp r4, #0
    beq _pow_zero_0
    cmp r4, #1
    beq _pow_fim_0
    sub r4, r4, #1
_pow_loop_0:
    vmul.f64 d0, d0, d2     @ d0 *= base
    subs r4, r4, #1
    bne _pow_loop_0
    b _pow_fim_0
_pow_zero_0:
    ldr r0, =const_um
    vldr.f64 d0, [r0]       @ d0 = 1.0
_pow_fim_0:
    vpush {d0}
    @ --- Armazenar resultado da linha 3 (slot 2) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #16      @ offset = slot 2 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 4: ( ( ( 100.0 3.0 // ) ( 2.0 8.0 ^ ) + ) 2.0 / ) ---
    @ Push 100.0
    ldr r0, =const_6
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 3.0
    ldr r0, =const_7
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '//' (divisão inteira)
    vpop {d1}              @ d1 = B
    vpop {d0}              @ d0 = A
    vdiv.f64 d0, d0, d1     @ d0 = A / B
    vcvt.s32.f64 s4, d0     @ s4 = truncar para int32
    vcvt.f64.s32 d0, s4     @ d0 = de volta para double
    vpush {d0}
    @ Push 2.0
    ldr r0, =const_8
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 8.0
    ldr r0, =const_9
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '^' (potência por loop)
    vpop {d1}              @ d1 = B (expoente)
    vpop {d0}              @ d0 = A (base)
    vcvt.s32.f64 s4, d1     @ converter expoente para int32
    vmov r4, s4              @ r4 = expoente inteiro
    vmov.f64 d2, d0          @ d2 = base (backup)
    cmp r4, #0
    beq _pow_zero_1
    cmp r4, #1
    beq _pow_fim_1
    sub r4, r4, #1
_pow_loop_1:
    vmul.f64 d0, d0, d2     @ d0 *= base
    subs r4, r4, #1
    bne _pow_loop_1
    b _pow_fim_1
_pow_zero_1:
    ldr r0, =const_um
    vldr.f64 d0, [r0]       @ d0 = 1.0
_pow_fim_1:
    vpush {d0}
    @ Operador '+' (soma)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vadd.f64 d0, d0, d1  @ d0 = A + B
    vpush {d0}
    @ Push 2.0
    ldr r0, =const_10
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '/' (divisão real)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vdiv.f64 d0, d0, d1  @ d0 = A / B
    vpush {d0}
    @ --- Armazenar resultado da linha 4 (slot 3) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #24      @ offset = slot 3 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 5: ( ( 45.5 2.5 - ) TEMPORARIO ) ---
    @ Push 45.5
    ldr r0, =const_11
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 2.5
    ldr r0, =const_12
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '-' (subtração)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vsub.f64 d0, d0, d1  @ d0 = A - B
    vpush {d0}
    @ Salvar em variável TEMPORARIO
    vpop {d0}
    ldr r1, =var_TEMPORARIO
    vstr.f64 d0, [r1]
    vpush {d0}             @ manter na pilha como resultado
    @ --- Armazenar resultado da linha 5 (slot 4) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #32      @ offset = slot 4 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 6: ( ( TEMPORARIO ) 10.0 / ) ---
    @ Ler variável TEMPORARIO
    ldr r0, =var_TEMPORARIO
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 10.0
    ldr r0, =const_13
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '/' (divisão real)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vdiv.f64 d0, d0, d1  @ d0 = A / B
    vpush {d0}
    @ --- Armazenar resultado da linha 6 (slot 5) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #40      @ offset = slot 5 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 7: ( 2 RES ) ---
    @ RES: resultado de 2 linha(s) atrás (slot 4)
    ldr r0, =resultados
    add r0, r0, #32
    vldr.f64 d0, [r0]
    vpush {d0}
    @ --- Armazenar resultado da linha 7 (slot 6) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #48      @ offset = slot 6 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 8: ( ( ( 2 RES ) ( TEMPORARIO ) * ) 0.5 + ) ---
    @ RES: resultado de 2 linha(s) atrás (slot 5)
    ldr r0, =resultados
    add r0, r0, #40
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Ler variável TEMPORARIO
    ldr r0, =var_TEMPORARIO
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '*' (multiplicação)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vmul.f64 d0, d0, d1  @ d0 = A * B
    vpush {d0}
    @ Push 0.5
    ldr r0, =const_16
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '+' (soma)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vadd.f64 d0, d0, d1  @ d0 = A + B
    vpush {d0}
    @ --- Armazenar resultado da linha 8 (slot 7) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #56      @ offset = slot 7 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 9: ( ( ( ( TEMPORARIO ) 2.0 * ) 3.0 ^ ) 5.0 % ) ---
    @ Ler variável TEMPORARIO
    ldr r0, =var_TEMPORARIO
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Push 2.0
    ldr r0, =const_17
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '*' (multiplicação)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vmul.f64 d0, d0, d1  @ d0 = A * B
    vpush {d0}
    @ Push 3.0
    ldr r0, =const_18
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '^' (potência por loop)
    vpop {d1}              @ d1 = B (expoente)
    vpop {d0}              @ d0 = A (base)
    vcvt.s32.f64 s4, d1     @ converter expoente para int32
    vmov r4, s4              @ r4 = expoente inteiro
    vmov.f64 d2, d0          @ d2 = base (backup)
    cmp r4, #0
    beq _pow_zero_2
    cmp r4, #1
    beq _pow_fim_2
    sub r4, r4, #1
_pow_loop_2:
    vmul.f64 d0, d0, d2     @ d0 *= base
    subs r4, r4, #1
    bne _pow_loop_2
    b _pow_fim_2
_pow_zero_2:
    ldr r0, =const_um
    vldr.f64 d0, [r0]       @ d0 = 1.0
_pow_fim_2:
    vpush {d0}
    @ Push 5.0
    ldr r0, =const_19
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '%' (resto via fmod)
    vpop {d1}              @ d1 = B
    vpop {d0}              @ d0 = A
    vdiv.f64 d2, d0, d1     @ d2 = A / B
    vcvt.s32.f64 s6, d2     @ s6 = trunc(A/B) como int32
    vcvt.f64.s32 d2, s6     @ d2 = trunc(A/B) como double
    vmul.f64 d2, d2, d1     @ d2 = trunc(A/B) * B
    vsub.f64 d0, d0, d2     @ d0 = A - trunc(A/B)*B = resto
    vpush {d0}
    @ --- Armazenar resultado da linha 9 (slot 8) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #64      @ offset = slot 8 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Linha 10: ( ( ( 1 RES ) ( 2 RES ) + ) ( 3 RES ) * ) ---
    @ RES: resultado de 1 linha(s) atrás (slot 8)
    ldr r0, =resultados
    add r0, r0, #64
    vldr.f64 d0, [r0]
    vpush {d0}
    @ RES: resultado de 2 linha(s) atrás (slot 7)
    ldr r0, =resultados
    add r0, r0, #56
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '+' (soma)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vadd.f64 d0, d0, d1  @ d0 = A + B
    vpush {d0}
    @ RES: resultado de 3 linha(s) atrás (slot 6)
    ldr r0, =resultados
    add r0, r0, #48
    vldr.f64 d0, [r0]
    vpush {d0}
    @ Operador '*' (multiplicação)
    vpop {d1}              @ d1 = B (topo)
    vpop {d0}              @ d0 = A (segundo)
    vmul.f64 d0, d0, d1  @ d0 = A * B
    vpush {d0}
    @ --- Armazenar resultado da linha 10 (slot 9) ---
    vpop {d0}              @ d0 = resultado da expressão
    ldr r1, =resultados
    add r1, r1, #72      @ offset = slot 9 * 8 bytes
    vstr.f64 d0, [r1]       @ salvar double no array
    ldr r2, =num_resultados
    ldr r3, [r2]
    add r3, r3, #1
    str r3, [r2]

@ --- Fim do programa ---
@ Resultados no array 'resultados' na .data

_halt:
    b _halt                  @ Loop infinito (inspecionar no debugger)
