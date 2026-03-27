# Compilador RPN para Assembly ARMv7 (Fase 1)

**Instituição:** PUCPR 
**Disciplina:** Construtor de Interpretadores
**Professor:** Frank 

**Integrantes do Grupo (Ordem Alfabética):**
* [Leonardo dos Santos Marques] - GitHub: [@leomrqs]

---

## Descrição do Projeto
Inclui um analisador léxico estrito baseado em Autómatos Finitos Determinísticos (implementado com funções de transição de estado, sem utilização de Expressões Regulares) e um gerador de código Back-End. O programa lê ficheiros de texto contendo expressões matemáticas e comandos de memória em Notação Polonesa Reversa (RPN) e traduz para código Assembly (FPU IEEE 754 64-bit) executável na arquitetura ARMv7 DEC1-SOC.

## Como Compilar e Executar
O programa foi desenvolvido em **Python 3** e não requer um passo prévio de compilação do código-fonte.

Para processar um ficheiro de teste e gerar o Assembly, abra o terminal no diretório do projeto e execute:

```bash
python main.py teste1.txt
python main.py teste2.txt
python main.py teste3.txt
