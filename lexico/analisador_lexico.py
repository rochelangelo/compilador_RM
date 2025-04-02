import re

class Token:
    def __init__(self, tipo, lexema):
        self.tipo = tipo
        self.lexema = lexema
    def __repr__(self):
        return f"Token({self.tipo}, {self.lexema})"

# Lista de palavras reservadas
PALAVRAS_RESERVADAS = {
    'inicio_programa': 'START',
    'fim_programa': 'END',
    'inteiro': 'INT',
    'booleano': 'BOOL',
    'texto': 'STRING',
    'funcao': 'FUN',
    'procedimento': 'PROC',
    'se': 'IF',
    'senao': 'ELSE',
    'escreva': 'PRINT',
    'verdadeiro': 'BOOLEAN',
    'falso': 'BOOLEAN',
    'retorne': 'RETURN',
    'enquanto': 'WHILE',
    'continue': 'CONTINUE',
    'pare': 'BREAK',
    'e': 'AND',
    'ou': 'OR',
}

# Tabela de regex para símbolos e operadores
PADROES = [
    ('IGUAL', r'=='),
    ('ATRIBUICAO', r'='),
    ('DIFERENTE', r'!='),
    ('MENORIGUAL', r'<='),
    ('MAIORIGUAL', r'>='),
    ('MENOR', r'<'),
    ('MAIOR', r'>'),
    ('SOMA', r'\+'),
    ('SUB', r'-'),
    ('MULT', r'\*'),
    ('DIV', r'/'),
    ('NOT', r'\!'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('VIRGULA', r','),
    ('PONTOVIRGULA', r';'),
    ('DOISPONTOS', r':'),
]

def analisar_codigo(codigo):
    tokens = []
    pos = 0

    while pos < len(codigo):
        if codigo[pos].isspace():
            pos += 1
            continue

        # Comentários entre chaves
        # if codigo[pos] == '{':
        #     end = codigo.find('}', pos)
        #     if end == -1:
        #         raise SyntaxError("Comentário não fechado")
        #     pos = end + 1
        #     continue

        # Números
        match = re.match(r'\d+', codigo[pos:])
        if match:
            lexema = match.group(0)
            tokens.append(Token('NUMERO', lexema))
            pos += len(lexema)
            continue

        # Identificadores e palavras reservadas
        match = re.match(r'[a-zA-Z_][a-zA-Z0-9_]*', codigo[pos:])
        if match:
            lexema = match.group(0)
            tipo = PALAVRAS_RESERVADAS.get(lexema, 'ID')
            tokens.append(Token(tipo, lexema))
            pos += len(lexema)
            continue

        # Operadores e símbolos
        matched = False
        for tipo, padrao in PADROES:
            regex = re.compile(padrao)
            match = regex.match(codigo[pos:])
            if match:
                lexema = match.group(0)
                tokens.append(Token(tipo, lexema))
                pos += len(lexema)
                matched = True
                break
        if matched:
            continue

        raise SyntaxError(f"Caractere inválido na posição {pos}: '{codigo[pos]}'")

    tokens.append(Token('EOF', 'EOF'))
    return tokens