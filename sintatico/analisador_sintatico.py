class TabelaSimbolos:
    def __init__(self):
        self.simbolos = {}

    def adicionar(self, nome, tipo, categoria):
        if nome in self.simbolos:
            raise Exception(f"Erro semântico: identificador '{nome}' já declarado.")
        self.simbolos[nome] = {
            'tipo': tipo,
            'categoria': categoria
        }

    def buscar(self, nome):
        if nome not in self.simbolos:
            raise Exception(f"Erro semântico: identificador '{nome}' não declarado.")
        return self.simbolos[nome]

    def existe(self, nome):
        return nome in self.simbolos

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.tabela = TabelaSimbolos()

    def token_atual(self):
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            return token.tipo, token.lexema
        return ('EOF', '')

    def consumir(self, esperado):
        tipo, lexema = self.token_atual()
        if tipo == esperado:
            self.pos += 1
            return True
        else:
            self.erro(f"Esperado '{esperado}', mas encontrado '{tipo}' ({lexema})")

    def erro(self, msg):
        raise SyntaxError(f"Erro sintático na posição {self.pos}: {msg}")

    def analisar(self):
        self.programa()

        if self.token_atual()[0] != 'EOF':
            self.erro(f"Tokens inesperados após 'fim de programa'. Encontrado '{self.token_atual()[0]}' ({self.token_atual()[1]})")

    def programa(self):
        self.consumir('START')
        self.consumir('ID')
        self.corpo()
        self.consumir('END')

    def corpo(self):
        while self.token_atual()[0] in ('INT', 'BOOL', 'STRING', 'FUN', 'PROC'):
            self.declaracao()

        while self.token_atual()[0] in ('ID', 'PRINT', 'IF', 'WHILE'):
            self.comando()

    def declaracao(self):
        tipo, _ = self.token_atual()
        if tipo in ('INT', 'BOOL', 'STRING'):
            self.declaracao_variaveis()
        elif tipo == 'FUN':
            self.declaracao_funcao()
        elif tipo == 'PROC':
            self.declaracao_procedimento()

    def declaracao_variaveis(self):
        tipo_token, _ = self.token_atual()
        self.tipo()
        tipo = tipo_token

        self.adicionar_simbolo_variavel(tipo)

        while self.token_atual()[0] == 'VIRGULA':
            self.consumir('VIRGULA')
            self.adicionar_simbolo_variavel(tipo)

        self.consumir('PONTOVIRGULA')

    def adicionar_simbolo_variavel(self, tipo):
        _, nome = self.token_atual()
        self.consumir('ID')
        self.tabela.adicionar(nome, tipo, 'variavel')

    def tipo(self):
        tipo, _ = self.token_atual()
        if tipo in ('INT', 'BOOL', 'STRING'):
            self.consumir(tipo)
        else:
            self.erro(f"Tipo inválido: {tipo}")

    def declaracao_funcao(self):
        self.consumir('FUN')
        _, nome = self.token_atual()
        self.consumir('ID')
        self.consumir('LPAREN')

        escopo_anterior = self.tabela
        self.tabela = TabelaSimbolos()

        self.parametros()
        self.consumir('RPAREN')
        self.consumir('DOISPONTOS')
        tipo_token, _ = self.token_atual()
        self.tipo()
        self.consumir('LBRACE')
        self.corpo()
        self.consumir('RBRACE')

        self.tabela = escopo_anterior

    def declaracao_procedimento(self):
        self.consumir('PROC')
        _, nome = self.token_atual()
        self.consumir('ID')
        self.consumir('LPAREN')

        escopo_anterior = self.tabela
        self.tabela = TabelaSimbolos()

        self.parametros()
        self.consumir('RPAREN')


        escopo_anterior.adicionar(nome, 'VOID', 'procedimento')

        self.consumir('LBRACE')
        self.corpo()
        self.consumir('RBRACE')


        self.tabela = escopo_anterior

    def parametros(self):
        if self.token_atual()[0] in ('INT', 'BOOL', 'STRING'):
            tipo_token, _ = self.token_atual()
            self.tipo()
            _, nome = self.token_atual()
            self.consumir('ID')
            self.tabela.adicionar(nome, tipo_token, 'parametro')  # adiciona a tabela o simbolo lido

            while self.token_atual()[0] == 'VIRGULA':
                self.consumir('VIRGULA')
                tipo_token, _ = self.token_atual()
                self.tipo()
                _, nome = self.token_atual()
                self.consumir('ID')
                self.tabela.adicionar(nome, tipo_token, 'parametro') # mesma coisa aqui, adiciona

    def comando(self):
        tipo, _ = self.token_atual()
        if tipo == 'ID':
            self.atribuicao()
        elif tipo == 'PRINT':
            self.comando_escreva()
        elif tipo == 'IF':
            self.comando_condicional()
        elif tipo == 'WHILE':
            self.comando_enquanto()

    def atribuicao(self):
        _, nome = self.token_atual()
        self.tabela.buscar(nome)  # Verifica se a variável foi declarada
        self.consumir('ID')
        self.consumir('ATRIBUICAO')
        self.expressao()
        self.consumir('PONTOVIRGULA')

    def comando_escreva(self):
        self.consumir('PRINT')
        self.consumir('LPAREN')
        self.expressao()
        self.consumir('RPAREN')
        self.consumir('PONTOVIRGULA')

    def comando_condicional(self):
        self.consumir('IF')
        self.consumir('LPAREN')
        self.expressao()
        self.consumir('RPAREN')
        self.consumir('LBRACE')
        self.corpo()
        self.consumir('RBRACE')
        if self.token_atual()[0] == 'ELSE':
            self.consumir('ELSE')
            self.consumir('LBRACE')
            self.corpo()
            self.consumir('RBRACE')

    def comando_enquanto(self):
        self.consumir('WHILE')
        self.consumir('LPAREN')
        self.expressao()
        self.consumir('RPAREN')
        self.consumir('LBRACE')
        self.corpo()
        self.consumir('RBRACE')

    def expressao(self):
        self.expressao_or()

    def expressao_or(self):
        self.expressao_and()
        while self.token_atual()[0] == 'OR':
            self.consumir('OR')
            self.expressao_and()

    def expressao_and(self):
        self.expressao_relacional()
        while self.token_atual()[0] == 'AND':
            self.consumir('AND')
            self.expressao_relacional()

    def expressao_relacional(self):
        self.expressao_soma()
        while self.token_atual()[0] in ('IGUAL', 'DIFERENTE', 'MENOR', 'MAIOR', 'MENORIGUAL', 'MAIORIGUAL'):
            self.consumir(self.token_atual()[0])
            self.expressao_soma()

    def expressao_soma(self):
        self.expressao_termo()
        while self.token_atual()[0] in ('SOMA', 'SUB'):
            self.consumir(self.token_atual()[0])
            self.expressao_termo()

    def expressao_termo(self):
        self.expressao_fator()
        while self.token_atual()[0] in ('MULT', 'DIV'):
            self.consumir(self.token_atual()[0])
            self.expressao_fator()

    def expressao_fator(self):
        tipo, _ = self.token_atual()
        if tipo == 'ID':
            _, nome = self.token_atual()
            self.tabela.buscar(nome)  # Verifica se foi declarado
            self.consumir('ID')
        elif tipo in ('NUMERO', 'BOOLEAN', 'STRING_LITERAL'):
            self.consumir(tipo)
        elif tipo == 'LPAREN':
            self.consumir('LPAREN')
            self.expressao()
            self.consumir('RPAREN')
        else:
            self.erro(f"Expressão inválida. Encontrado {tipo}")
