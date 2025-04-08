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
        self.avaliando_argumentos = False

        # 🔽 Aqui sim!
        self.codigo_intermediario = []
        self.temp_count = 0
        self.label_count = 0
    
    def novo_temp(self):
        temp = f"_t{self.temp_count}"
        self.temp_count += 1
        return temp
    
    def novo_label(self):
        label = f"L{self.label_count}"
        self.label_count += 1
        return label


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
        
        print("\n✓ Código analisado com sucesso!")
        print("\nCódigo de três endereços gerado:")
        for linha in self.codigo_intermediario:
            print(linha)


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
            nome = lexema

            if not self.tabela.existe(nome):
                raise Exception(f"Erro semântico: identificador '{nome}' não declarado no escopo '{self.tabela.escopo}'.")

            # 🔒 Proteção contra loop de chamadas aninhadas infinitas
            if (
                not self.avaliando_argumentos and
                self.pos + 1 < len(self.tokens) and
                self.tokens[self.pos + 1].tipo == 'LPAREN'
            ):
                return self.chamada_funcao_com_retorno()

            simbolo = self.tabela.buscar(nome)
            self.consumir('ID')
            return simbolo['tipo']

        elif tipo == 'LPAREN':
            self.consumir('LPAREN')
            tipo_expressao = self.expressao()
            self.consumir('RPAREN')
            return tipo_expressao

        else:
            self.erro(f"Expressão inválida: {lexema}")
            return 'ERRO'




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
        tipo, lexema = self.token_atual()

        if tipo == 'ID':
            # Corrigido para acessar corretamente o tipo do próximo token
            proximo_tipo = self.tokens[self.pos + 1].tipo

            if proximo_tipo == 'ATRIBUICAO':
                self.atribuicao()
            elif proximo_tipo == 'LPAREN':
                self.chamada_procedimento()
                self.consumir('PONTOVIRGULA')
            else:
                self.erro(f"Comando inválido iniciado por identificador: '{lexema}'")

        elif tipo == 'PRINT':
            self.comando_escreva()
        elif tipo == 'IF':
            self.comando_condicional()
        elif tipo == 'WHILE':
            self.comando_enquanto()
        elif tipo == 'RETURN':
            self.comando_retorno()

            
    def chamada_procedimento(self):
        _, nome = self.token_atual()

        if not self.tabela.existe(nome):
            raise Exception(f"Erro semântico: procedimento ou função '{nome}' não declarado.")

        simbolo = self.tabela.buscar(nome)

        if simbolo['categoria'] not in ('funcao', 'procedimento'):
            raise Exception(f"Erro semântico: '{nome}' não é uma função nem procedimento.")

        self.consumir('ID')
        self.consumir('LPAREN')

        self.argumentos()

        self.consumir('RPAREN')
        
    def argumentos(self):
        if self.token_atual()[0] != 'RPAREN':
            while True:
                self.expressao()
                if self.token_atual()[0] != 'VIRGULA':
                    break
                self.consumir('VIRGULA')

        



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

        resultado = self.expressao()

        if not self.tipos_compativeis(simbolo['tipo'], resultado['tipo']):
            raise Exception(f"Erro semântico: atribuição inválida. Esperado '{simbolo['tipo']}', mas encontrado '{resultado['tipo']}'.")

        self.codigo_intermediario.append(f"{nome} := {resultado['lugar']}")

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
        resultado = self.expressao()  # resultado = {'tipo': ..., 'lugar': ...}
        self.consumir('RPAREN')
        self.consumir('PONTOVIRGULA')

        self.codigo_intermediario.append(f"escreva({resultado['lugar']})")


    def comando_condicional(self):
        self.consumir('IF')
        self.consumir('LPAREN')
        cond = self.expressao()  # retorno: {'tipo', 'lugar'}
        self.consumir('RPAREN')

        if cond['tipo'] != 'BOOL':
            self.erro("A condição do 'se' deve ser booleana.")

        label_verdadeiro = self.novo_label()
        label_falso = self.novo_label()
        label_fim = self.novo_label()

        # if condicao goto L_verdadeiro
        self.codigo_intermediario.append(f"if {cond['lugar']} goto {label_verdadeiro}")
        self.codigo_intermediario.append(f"goto {label_falso}")

        # L_verdadeiro:
        self.codigo_intermediario.append(f"{label_verdadeiro}:")

        self.consumir('LBRACE')
        self.corpo()
        self.consumir('RBRACE')

        # depois do bloco verdadeiro, ir pro fim (caso tenha else)
        self.codigo_intermediario.append(f"goto {label_fim}")

        # L_falso:
        self.codigo_intermediario.append(f"{label_falso}:")

        if self.token_atual()[0] == 'ELSE':
            self.consumir('ELSE')
            self.consumir('LBRACE')
            self.corpo()
            self.consumir('RBRACE')

        # L_fim:
        self.codigo_intermediario.append(f"{label_fim}:")


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
        esquerda = self.expressao_termo()

        # Operadores aritméticos (+ e -)
        while self.token_atual() and self.token_atual()[0] in ('SOMA', 'SUB'):
            operador = self.token_atual()[0]
            self.consumir(operador)

            direita = self.expressao_termo()

            if esquerda['tipo'] != 'INT' or direita['tipo'] != 'INT':
                self.erro(f"Operador '{operador}' espera inteiros, mas recebeu {esquerda['tipo']} e {direita['tipo']}")

            op_simbolo = '+' if operador == 'SOMA' else '-'
            temp = self.novo_temp()
            self.codigo_intermediario.append(f"{temp} := {esquerda['lugar']} {op_simbolo} {direita['lugar']}")

            esquerda = {'tipo': 'INT', 'lugar': temp}

        # Operadores relacionais
        if self.token_atual() and self.token_atual()[0] in ('IGUAL', 'DIFERENTE', 'MENOR', 'MAIOR', 'MENORIGUAL', 'MAIORIGUAL'):
            operador = self.token_atual()[0]
            self.consumir(operador)

            direita = self.expressao_termo()

            if esquerda['tipo'] != direita['tipo']:
                self.erro(f"Operador relacional '{operador}' usado com tipos incompatíveis: {esquerda['tipo']} e {direita['tipo']}")

            temp = self.novo_temp()
            op_map = {
                'IGUAL': '==',
                'DIFERENTE': '!=',
                'MENOR': '<',
                'MAIOR': '>',
                'MENORIGUAL': '<=',
                'MAIORIGUAL': '>='
            }
            self.codigo_intermediario.append(f"{temp} := {esquerda['lugar']} {op_map[operador]} {direita['lugar']}")
            esquerda = {'tipo': 'BOOL', 'lugar': temp}

        # Operadores lógicos (AND, OR)
        while self.token_atual() and self.token_atual()[0] in ('AND', 'OR'):
            operador = self.token_atual()[0]
            self.consumir(operador)

            direita = self.expressao_termo()

            if esquerda['tipo'] != 'BOOL' or direita['tipo'] != 'BOOL':
                self.erro(f"Operador lógico '{operador}' espera booleanos, mas recebeu {esquerda['tipo']} e {direita['tipo']}")

            temp = self.novo_temp()
            op = '&&' if operador == 'AND' else '||'
            self.codigo_intermediario.append(f"{temp} := {esquerda['lugar']} {op} {direita['lugar']}")
            esquerda = {'tipo': 'BOOL', 'lugar': temp}

        return esquerda

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
    
    def chamada_funcao_com_retorno(self):
        _, nome = self.token_atual()
        simbolo = self.tabela.buscar(nome)

        if simbolo['categoria'] != 'funcao':
            raise Exception(f"Erro semântico: '{nome}' não é uma função e não pode ser usada em expressões.")

        self.consumir('ID')
        self.consumir('LPAREN')

        parametros_esperados = simbolo.get('parametros', [])
        argumentos_recebidos = []

        # 🛡️ Ativa proteção contra recursão infinita
        self.avaliando_argumentos = True

        if self.token_atual()[0] != 'RPAREN':
            while True:
                tipo = self.expressao()
                argumentos_recebidos.append(tipo)
                if self.token_atual()[0] != 'VIRGULA':
                    break
                self.consumir('VIRGULA')

        self.avaliando_argumentos = False  # 🛡️ Desativa ao sair da chamada

        self.consumir('RPAREN')

        if len(argumentos_recebidos) != len(parametros_esperados):
            raise Exception(f"Erro semântico: função '{nome}' espera {len(parametros_esperados)} argumentos, mas recebeu {len(argumentos_recebidos)}.")

        for (param_nome, param_tipo), tipo_recebido in zip(parametros_esperados, argumentos_recebidos):
            if param_tipo != tipo_recebido:
                raise Exception(f"Erro semântico: tipo do argumento incompatível em '{nome}'. Esperado '{param_tipo}', mas recebeu '{tipo_recebido}'.")

        return simbolo['retorno']


    def expressao_fator(self):
        tipo, lexema = self.token_atual()

        if tipo == 'ID':
            nome = lexema

            if not self.tabela.existe(nome):
                raise Exception(f"Erro semântico: identificador '{nome}' não declarado.")

            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].tipo == 'LPAREN':
                return self.chamada_funcao_com_retorno()

            simbolo = self.tabela.buscar(nome)
            self.consumir('ID')
            return { 'tipo': simbolo['tipo'], 'lugar': nome }

        elif tipo == 'NUMERO':
            self.consumir('NUMERO')
            return { 'tipo': 'INT', 'lugar': lexema }

        elif tipo == 'STRING_LITERAL':
            self.consumir('STRING_LITERAL')
            return { 'tipo': 'STRING', 'lugar': lexema }

        elif tipo == 'TRUE' or tipo == 'FALSE':
            self.consumir(tipo)
            return { 'tipo': 'BOOL', 'lugar': lexema }

        elif tipo == 'LPAREN':
            self.consumir('LPAREN')
            resultado = self.expressao()
            self.consumir('RPAREN')
            return resultado

        else:
            self.erro(f"Erro semântico: Token inesperado na expressão: {tipo} ({lexema})")
            return { 'tipo': 'ERRO', 'lugar': '?' }



