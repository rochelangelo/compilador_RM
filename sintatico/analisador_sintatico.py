class TabelaSimbolos:
    def __init__(self, escopo='global', anterior=None):
        self.simbolos = {}
        self.escopo = escopo
        self.anterior = anterior # para referência ao escopo anterior
    
    class TabelaSimbolos:
    
     def verificarCondicao(self, identificador):
        """
        Verifica se um identificador existe no escopo atual ou no global.

        Args:
            identificador (str): Nome do identificador a ser buscado.

        Returns:
            dict: Entrada correspondente na tabela de símbolos, se encontrada.

        Raises:
            Exception: Se o identificador não for encontrado.
        """
        # Primeiro, verifica no escopo atual
        if identificador in self.simbolos:
            return self.simbolos[identificador]

        # Se não estiver no escopo atual, busca no escopo anterior (escopo global ou mais acima)
        if self.anterior:
            return self.anterior.verificarCondicao(identificador)

        # Se não for encontrado, lança um erro
        raise Exception(f"Erro semântico: identificador '{identificador}' não declarado no escopo '{self.escopo}'.")


    def adicionar(self, nome, tipo, categoria, parametros=None, retorno=None):
        if self.existe(nome):
            raise Exception(f"Erro semântico: identificador '{nome}' já declarado no escopo '{self.escopo}'.")
        
        self.simbolos[nome] = {
            'tipo': tipo,
            'categoria': categoria,
            'parametros': parametros,
            'retorno': retorno
        }


    def buscar(self, nome):
        print(f"Buscando '{nome}' no escopo '{self.escopo}'")  # DEBUG
        if nome in self.simbolos:
            return self.simbolos[nome]
        elif self.anterior:  # Busca no escopo anterior
            return self.anterior.buscar(nome)
        else:
            raise Exception(f"Erro semântico: identificador '{nome}' não declarado no escopo '{self.escopo}'.")


    def existe(self, nome):
        if nome in self.simbolos:
            return True
        elif self.anterior:
            return self.anterior.existe(nome)
        return False

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
        
        while True:  # Permitir múltiplas variáveis separadas por vírgula
            _, nome = self.token_atual()
            self.consumir('ID')
            self.tabela.adicionar(nome, tipo, 'variavel')
            
            if self.token_atual()[0] != 'VIRGULA':  
                break  # Sai do loop se não houver mais variáveis
            self.consumir('VIRGULA')  # Consome a vírgula e continua

        self.consumir('PONTOVIRGULA')  # Agora consome o ponto e vírgula no final da linha


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
        print(f"Tabela de símbolos no início da função '{nome}': {self.tabela.simbolos}")
        self.consumir('ID')
        self.consumir('LPAREN')

        parametros = self.parametros()
        
        self.consumir('RPAREN')
        self.consumir('DOISPONTOS')
        tipo_retorno, _ = self.token_atual()

        if tipo_retorno not in ('INT', 'BOOL', 'STRING'):
            self.erro(f"Tipo inválido de retorno para função: {tipo_retorno}")

        self.tipo()
        self.consumir('LBRACE')

        # Criar novo escopo e adicionar à tabela de símbolos
        escopo_anterior = self.tabela
        self.tabela = TabelaSimbolos(escopo=nome, anterior=escopo_anterior)

        # Adicionar parâmetros à tabela da função (escopo local)
        for param_nome, param_tipo in parametros:
            print(f"Adicionando parâmetro '{param_nome}' do tipo '{param_tipo}' ao escopo '{nome}'")  # DEBUG
            self.tabela.adicionar(param_nome, param_tipo, 'parametro')

        # Registrar a função no escopo global
        escopo_anterior.adicionar(nome, tipo_retorno, 'funcao', parametros, tipo_retorno)

        print(f"Tabela de símbolos dentro da função '{nome}': {self.tabela.simbolos}")  # Debug

        self.corpo()
        self.consumir('RBRACE')

        # Restaurar escopo anterior
        self.tabela = escopo_anterior

        

    def declaracao_procedimento(self):
        self.consumir('PROC')
        _, nome = self.token_atual()
        self.consumir('ID')
        self.consumir('LPAREN')

        escopo_anterior = self.tabela
        self.tabela = TabelaSimbolos(escopo=nome, anterior=escopo_anterior)

        parametros = self.parametros()
        
        for param_nome, param_tipo in parametros:
            self.tabela.adicionar(param_nome, param_tipo, 'parametro')

        self.consumir('RPAREN')

        escopo_anterior.adicionar(nome, 'VOID', 'procedimento', parametros)

        self.consumir('LBRACE')
        self.corpo()
        self.consumir('RBRACE')

        self.tabela = escopo_anterior


    def parametros(self):
        parametros = []
        if self.token_atual()[0] != 'RPAREN':  # Há parâmetros
            while True:
                tipo, _ = self.token_atual()
                self.tipo()
                _, nome = self.token_atual()
                self.consumir('ID')
                parametros.append((nome, tipo))
                if self.token_atual()[0] != 'VIRGULA':
                    break
                self.consumir('VIRGULA')
        return parametros  # Retorna lista vazia caso não tenha parâmetros


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
        print(f"Verificando atribuição para '{nome}' no escopo '{self.tabela.escopo}'")  # DEBUG

        if not self.tabela.existe(nome):
            raise Exception(f"Erro semântico: identificador '{nome}' não declarado no escopo '{self.tabela.escopo}'.")

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
            
   

