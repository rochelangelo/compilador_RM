from lexico.analisador_lexico import analisar_codigo
from sintatico.analisador_sintatico import Parser

def main():
    with open("entrada.txt", "r", encoding="utf-8") as f:
        codigo = f.read()

    tokens = analisar_codigo(codigo)

    print("TOKENS LIDOS:")
    index = 0
    for t in tokens:
        print(f"{index} - {t}")
        index += 1

    parser = Parser(tokens)
    try:
        parser.analisar()
        print("✓ Código analisado com sucesso!")
    except Exception as e:
        print("✗ Erro durante análise:")
        print(e)

if __name__ == "__main__":
    main()
