class TabelaSimbolos:
    def __init__(self, escopo='global', anterior=None, tipo_retorno=None):
        self.simbolos = {}
        self.escopo = escopo
        self.anterior = anterior # para referência ao escopo anterior
        self.tipo_retorno = tipo_retorno


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

    def entrar_escopo(self, nome, tipo_retorno=None):
        self.escopos.append({
            'nome': nome,
            'simbolos': {},
            'retorno': tipo_retorno
        })

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.tabela = TabelaSimbolos()
        self.linha_atual = 1

    def token_atual(self):
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            return token.tipo, token.lexema
        return ('EOF', '')

    def posicao_token(self):
        return self.pos # Ou a variável correta que armazena a posição


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
        while self.token_atual()[0] not in ('RBRACE', 'END', 'EOF'):
            # print(f'{self.token_atual()[0]}')
            if self.token_atual()[0] in ('INT', 'BOOL', 'STRING', 'FUN', 'PROC'):
                self.declaracao()
            else:
                self.comando()

    def expressao_multiplicacao(self):
        self.expressao_unaria()
        while self.token_atual()[0] in ('MULT', 'DIV'):
            self.consumir(self.token_atual()[0])
            self.expressao_unaria()

    def expressao_unaria(self):
        if self.token_atual()[0] in ('SUB', 'NEGACAO'):
            self.consumir(self.token_atual()[0])
        self.expressao_primaria()

    def expressao_primaria(self):
        tipo, lexema = self.token_atual()

        if tipo == 'NUMERO':
            self.consumir('NUMERO')
            return 'INT'
        elif tipo == 'STRING_LITERAL':
            self.consumir('STRING_LITERAL')
            return 'STRING'
        elif tipo == 'TRUE' or tipo == 'FALSE':
            self.consumir(tipo)
            return 'BOOL'
        elif tipo == 'ID':
            _, nome = self.token_atual()
            if not self.tabela.existe(nome):
                raise Exception(f"Erro semântico: identificador '{nome}' não declarado no escopo '{self.tabela.escopo}'.")
            simbolo = self.tabela.buscar(nome)
            self.consumir('ID')
            if 'tipo' not in simbolo:
                raise Exception(f"Erro semântico: identificador '{nome}' não possui um tipo definido na tabela de símbolos.")
            return simbolo['tipo']
        elif tipo == 'LPAREN':
            self.consumir('LPAREN')
            tipo_expressao = self.expressao()
            self.consumir('RPAREN')
            return tipo_expressao
        else:
            self.erro(f"Expressão inválida: {lexema}")
            return None


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
        self.tabela = TabelaSimbolos(escopo=nome, anterior=escopo_anterior, tipo_retorno=tipo_retorno)

        # Adicionar parâmetros à tabela da função (escopo local)
        for param_nome, param_tipo in parametros:
            self.tabela.adicionar(param_nome, param_tipo, 'parametro')

        # Registrar a função no escopo global
        escopo_anterior.adicionar(nome, tipo_retorno, 'funcao', parametros, tipo_retorno)

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
        elif tipo == 'RETURN':
            self.comando_retorno()

    def tipos_compativeis(self, tipo_variavel, tipo_expressao):
        # somente tipos idênticos são compatíveis
        return tipo_variavel == tipo_expressao

        # Regras adicionais de conversão implícita, se aplicável
        # if tipo_variavel == 'INT' and tipo_expressao == 'BOOL':
        #     return True  # Exemplo: permitir atribuir um booleano a um inteiro
        # return False  # Caso contrário, a atribuição é inválida



    def atribuicao(self):
        _, nome = self.token_atual()

        if not self.tabela.existe(nome):
            raise Exception(f"Erro semântico: identificador '{nome}' não declarado no escopo '{self.tabela.escopo}'.")

        simbolo = self.tabela.buscar(nome)
        self.consumir('ID')
        self.consumir('ATRIBUICAO')

        tipo_expressao = self.expressao()


        if not self.tipos_compativeis(simbolo['tipo'], tipo_expressao):
            raise Exception(f"Erro semântico: atribuição inválida. Esperado '{simbolo['tipo']}', mas encontrado '{tipo_expressao}'.")


        if self.token_atual()[0] == 'PONTOVIRGULA':
            self.consumir('PONTOVIRGULA')



    def obter_tipo_retorno_funcao(self):
        for escopo in reversed(self.escopos):
            if 'retorno' in escopo and escopo['retorno'] is not None:
                return escopo['retorno']
        raise Exception("Comando 'retorna' fora de uma função com tipo de retorno.")

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

    def comando_retorno(self):
        self.consumir('RETURN')
        tipo = self.expressao()

        escopo_funcao = self.tabela
        while escopo_funcao and escopo_funcao.tipo_retorno is None:
            escopo_funcao = escopo_funcao.anterior

        if escopo_funcao is None:
            raise Exception("Comando 'return' fora de função")

        tipo_esperado = escopo_funcao.tipo_retorno

        if tipo != tipo_esperado:
            raise Exception(f"Tipo de retorno incompatível: esperado {tipo_esperado}, mas encontrado {tipo}")

    def expressao(self):

        tipo = self.expressao_termo()

        while self.token_atual() and self.token_atual()[0] in ('SOMA', 'SUB'):
            operador = self.token_atual()[0]  # Captura o operador para debug
            self.consumir(operador)

            tipo_direita = self.expressao_termo()

            if tipo != 'INT' or tipo_direita != 'INT':
                self.erro(f"Operador '{operador}' espera inteiros, mas recebeu {tipo} e {tipo_direita}")

            tipo = 'INT'


        # 🔹 Adicionando operadores relacionais
        if self.token_atual() and self.token_atual()[0] in ('IGUAL', 'DIFERENTE', 'MENOR', 'MAIOR', 'MENORIGUAL', 'MAIORIGUAL'):
            operador_relacional = self.token_atual()[0]
            self.consumir(operador_relacional)

            tipo_direita = self.expressao_termo()

            if tipo != tipo_direita:
                self.erro(f"Operador relacional '{operador_relacional}' usado com tipos incompatíveis: {tipo} e {tipo_direita}")

            tipo = 'BOOL'

        # 🔹 Adicionando operadores lógicos (AND, OR)
        while self.token_atual() and self.token_atual()[0] in ('AND', 'OR'):
            operador_logico = self.token_atual()[0]
            self.consumir(operador_logico)

            tipo_direita = self.expressao_termo()

            if tipo != 'BOOL' or tipo_direita != 'BOOL':
                self.erro(f"Operador lógico '{operador_logico}' espera booleanos, mas recebeu {tipo} e {tipo_direita}")

            tipo = 'BOOL'

        # Verifica se estamos dentro de um contexto que exige ';'
        if self.token_atual() and self.token_atual()[0] == 'PONTOVIRGULA':
            self.consumir('PONTOVIRGULA')
        elif self.token_atual() and self.token_atual()[0] == 'RPAREN':
            return tipo
        else:
            raise Exception(f"Erro sintático no token {self.pos} ({self.token_atual()}): "
                            f"Esperado 'PONTOVIRGULA' ou 'RPAREN', mas encontrado '{self.token_atual()[1] if self.token_atual() else 'EOF'}'.")

        return tipo

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

        tipo = self.expressao_fator()

        while self.token_atual() and self.token_atual()[0] in ('MULT', 'DIV'):
            operador = self.token_atual()[0]
            self.consumir(operador)


            tipo_direita = self.fator()

            if not self.tipos_compativeis(tipo, tipo_direita):
                raise Exception(f"Erro semântico: Operação inválida entre '{tipo}' e '{tipo_direita}'.")

        return tipo



    def expressao_fator(self):
        tipo, lexema = self.token_atual()


        if tipo == 'ID':
            # Busca na tabela de símbolos para obter o tipo do identificador
            simbolo = self.tabela.buscar(lexema)
            if simbolo is None:
                self.erro(f"Erro semântico: Variável '{lexema}' não declarada.")
            self.consumir('ID')
            return simbolo['tipo']

        elif tipo == 'NUMERO':
            self.consumir('NUMERO')
            return 'INT'

        elif tipo == 'STRING':
            self.consumir('STRING')
            return 'STRING'

        elif tipo == 'TRUE' or tipo == 'FALSE':
            self.consumir(tipo)
            return 'BOOL'

        elif tipo == 'LPAREN':
            self.consumir('LPAREN')
            tipo_expressao = self.expressao()
            self.consumir('RPAREN')
            return tipo_expressao

        else:
            self.erro(f"Erro semântico: Token inesperado na expressão: {tipo} ({lexema})")
            return 'ERRO'  # Evita que a função retorne None


