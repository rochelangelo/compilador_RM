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
        # self.avaliando_argumentos = False

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
            return self.tokens[self.pos]
            # return token.tipo, token.lexema
        return ('EOF', '')

    def posicao_token(self):
        return self.pos # Ou a variável correta que armazena a posição


    def consumir(self, esperado):
        token = self.token_atual()
        tipo = token.tipo
        lexema = token.lexema
        if tipo == esperado:
            self.pos += 1
            return True
        else:
            self.erro(f"Esperado '{esperado}', mas encontrado '{tipo}' ({lexema})")

    def erro(self, msg):
        raise SyntaxError(f"Erro sintático na posição {self.pos}: {msg}")

    def analisar(self):
        self.programa()

        if self.token_atual().tipo != 'EOF':
            token = self.token_atual()
            print(f"Token atual na posição {self.pos}: {token}")
            self.erro(f"Tokens inesperados após 'fim de programa'. Encontrado '{token.tipo}' ({token.lexema})")

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
        while self.token_atual().tipo not in ('RBRACE', 'END', 'EOF'):
            if self.token_atual().tipo in ('INT', 'BOOL', 'STRING', 'FUN', 'PROC'):
                self.declaracao()
            else:
                self.comando()


    def expressao_multiplicacao(self):
        self.expressao_unaria()
        while self.token_atual().tipo in ('MULT', 'DIV'):
            self.consumir(self.token_atual().tipo)
            self.expressao_unaria()

    def expressao_unaria(self):
        if self.token_atual().tipo in ('SUB', 'NEGACAO'):
            self.consumir(self.token_atual().tipo)
        self.expressao_fator()



    def declaracao(self):
        token = self.token_atual()
        tipo = token.tipo
        if tipo in ('INT', 'BOOL', 'STRING'):
            self.declaracao_variaveis()
        elif tipo == 'FUN':
            self.declaracao_funcao()
        elif tipo == 'PROC':
            self.declaracao_procedimento()

    def declaracao_variaveis(self):
        tipo_token = self.token_atual().tipo
        self.tipo()
        tipo = tipo_token

        while True:  # Permitir múltiplas variáveis separadas por vírgula
            nome = self.token_atual().lexema
            self.consumir('ID')
            self.tabela.adicionar(nome, tipo, 'variavel')

            if self.token_atual().tipo != 'VIRGULA':
                break  # Sai do loop se não houver mais variáveis
            self.consumir('VIRGULA')  # Consome a vírgula e continua

        self.consumir('PONTOVIRGULA')  # Agora consome o ponto e vírgula no final da linha


    def adicionar_simbolo_variavel(self, tipo):
        nome = self.token_atual().lexema
        self.consumir('ID')
        self.tabela.adicionar(nome, tipo, 'variavel')

    def tipo(self):
        token = self.token_atual()
        tipo = token.tipo
        if tipo in ('INT', 'BOOL', 'STRING'):
            self.consumir(tipo)
        else:
            self.erro(f"Tipo inválido: {tipo}")

    def declaracao_funcao(self):
        self.consumir('FUN')
        nome = self.token_atual().lexema
        self.consumir('ID')
        self.consumir('LPAREN')

        parametros = self.parametros()

        self.consumir('RPAREN')
        self.consumir('DOISPONTOS')
        tipo_retorno = self.token_atual().tipo

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


    def expressao_primaria(self):
        token = self.token_atual()
        tipo = token.tipo
        lexema = token.lexema

        if tipo == 'NUMERO':
            self.consumir('NUMERO')
            return { 'tipo': 'INT', 'lugar': lexema }

        elif tipo == 'STRING_LITERAL':
            self.consumir('STRING_LITERAL')
            return { 'tipo': 'STRING', 'lugar': lexema }

        elif tipo in ('TRUE', 'FALSE'):
            self.consumir(tipo)
            return { 'tipo': 'BOOL', 'lugar': lexema }

        elif tipo == 'ID':
            nome = lexema
            if not self.tabela.existe(nome):
                self.erro(f"Identificador '{nome}' não declarado.")

            # Função?
            # ⚠️ Só chama a função se ainda não estiver avaliando os argumentos da própria função
            # if (not self.avaliando_argumentos
            #     and self.pos + 1 < len(self.tokens)
            #     and self.tokens[self.pos + 1].tipo == 'LPAREN'):
            #     return self.chamada_funcao_com_retorno()

            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].tipo == 'LPAREN':
                return self.chamada_funcao_com_retorno()

            simbolo = self.tabela.buscar(nome)
            self.consumir('ID')
            return { 'tipo': simbolo['tipo'], 'lugar': nome }

        elif tipo == 'LPAREN':
            self.consumir('LPAREN')
            resultado = self.expressao()
            self.consumir('RPAREN')
            return resultado

        else:
            self.erro(f"Expressão inválida: {lexema}")
            return { 'tipo': 'ERRO', 'lugar': '?' }


    def declaracao_procedimento(self):
        self.consumir('PROC')
        nome = self.token_atual().lexema
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
        if self.token_atual().tipo != 'RPAREN':  # Há parâmetros
            while True:
                token_tipo = self.token_atual()
                tipo = token_tipo.tipo
                self.tipo()
                tokenn_id = self.token_atual()
                nome = tokenn_id.lexema
                self.consumir('ID')
                parametros.append((nome, tipo))
                if self.token_atual().tipo != 'VIRGULA':
                    break
                self.consumir('VIRGULA')
        return parametros  # Retorna lista vazia caso não tenha parâmetros


    def comando(self):
        token = self.token_atual()
        tipo = token.tipo
        lexema = token.lexema

        if tipo == 'ID':
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
        elif tipo == 'PONTOVIRGULA':
            self.consumir('PONTOVIRGULA')



    def chamada_procedimento(self):
        nome = self.token_atual().lexema

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
        args = []
        if self.token_atual().tipo != 'RPAREN':
            args.append(self.expressao())
            while self.token_atual().tipo == 'VIRGULA':
                self.consumir('VIRGULA')
                args.append(self.expressao())
        return args

    def tipos_compativeis(self, tipo_variavel, tipo_expressao):
        # somente tipos idênticos são compatíveis
        return tipo_variavel == tipo_expressao

        # Regras adicionais de conversão implícita, se aplicável
        # if tipo_variavel == 'INT' and tipo_expressao == 'BOOL':
        #     return True  # Exemplo: permitir atribuir um booleano a um inteiro
        # return False  # Caso contrário, a atribuição é inválida



    def atribuicao(self):
        nome = self.token_atual().lexema

        if not self.tabela.existe(nome):
            raise Exception(f"Identificador '{nome}' não declarado.")

        simbolo = self.tabela.buscar(nome)
        self.consumir('ID')
        self.consumir('ATRIBUICAO')

        resultado = self.expressao()

        if not resultado or 'tipo' not in resultado or 'lugar' not in resultado:
            raise Exception("Erro interno: expressão inválida ou incompleta durante atribuição.")

        if not self.tipos_compativeis(simbolo['tipo'], resultado['tipo']):
            raise Exception(f"Atribuição inválida: esperado '{simbolo['tipo']}', recebeu '{resultado['tipo']}'.")

        self.codigo_intermediario.append(f"{nome} := {resultado['lugar']}")

        # 🔐 CORREÇÃO IMPORTANTE: garante que o ponto e vírgula seja consumido corretamente
        if self.token_atual().tipo == 'PONTOVIRGULA':
            self.consumir('PONTOVIRGULA')
        else:
            raise Exception(f"Esperado ';' após atribuição, mas encontrado '{self.token_atual().lexema}'")


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

        if self.token_atual().tipo == 'ELSE':
            self.consumir('ELSE')
            self.consumir('LBRACE')
            self.corpo()
            self.consumir('RBRACE')

        # L_fim:
        self.codigo_intermediario.append(f"{label_fim}:")


    def comando_enquanto(self):
        self.consumir('WHILE')
        self.consumir('LPAREN')

        label_inicio = self.novo_label()
        label_corpo = self.novo_label()
        label_fim = self.novo_label()

        self.codigo_intermediario.append(f"{label_inicio}:")

        cond = self.expressao()  # retorno: {'tipo', 'lugar'}
        if cond['tipo'] != 'BOOL':
            self.erro("A condição do 'enquanto' deve ser booleana.")

        self.consumir('RPAREN')

        self.codigo_intermediario.append(f"if {cond['lugar']} goto {label_corpo}")
        self.codigo_intermediario.append(f"goto {label_fim}")
        self.codigo_intermediario.append(f"{label_corpo}:")

        self.consumir('LBRACE')
        self.corpo()
        self.consumir('RBRACE')

        self.codigo_intermediario.append(f"goto {label_inicio}")
        self.codigo_intermediario.append(f"{label_fim}:")

    def comando_retorno(self):
        self.consumir('RETURN')
        valor = self.expressao()

        escopo_funcao = self.tabela
        while escopo_funcao and escopo_funcao.tipo_retorno is None:
            escopo_funcao = escopo_funcao.anterior

        if escopo_funcao is None:
            raise Exception("Comando 'return' fora de função")

        if valor['tipo'] != escopo_funcao.tipo_retorno:
            raise Exception(f"Tipo de retorno incompatível: esperado {escopo_funcao.tipo_retorno}, mas encontrado {valor['tipo']}")

        self.codigo_intermediario.append(f"return {valor['lugar']}")


    def expressao(self):
        esquerda = self.expressao_termo()

        # Operadores aritméticos (+ e -)
        while self.pos < len(self.tokens) and self.token_atual().tipo in ('SOMA', 'SUB'):
            operador = self.token_atual().tipo
            self.consumir(operador)

            direita = self.expressao_termo()

            if esquerda['tipo'] != 'INT' or direita['tipo'] != 'INT':
                self.erro(f"Operador '{operador}' espera inteiros, mas recebeu {esquerda['tipo']} e {direita['tipo']}")

            op_simbolo = '+' if operador == 'SOMA' else '-'
            temp = self.novo_temp()
            self.codigo_intermediario.append(f"{temp} := {esquerda['lugar']} {op_simbolo} {direita['lugar']}")
            esquerda = { 'tipo': 'INT', 'lugar': temp }

        # Operadores relacionais
        if self.token_atual() and self.token_atual().tipo in ('IGUAL', 'DIFERENTE', 'MENOR', 'MAIOR', 'MENORIGUAL', 'MAIORIGUAL'):
            operador = self.token_atual().tipo
            self.consumir(operador)

            direita = self.expressao_termo()

            if esquerda['tipo'] != direita['tipo']:
                self.erro(f"Operador relacional '{operador}' usado com tipos incompatíveis: {esquerda['tipo']} e {direita['tipo']}")

            op_map = {
                'IGUAL': '==',
                'DIFERENTE': '!=',
                'MENOR': '<',
                'MAIOR': '>',
                'MENORIGUAL': '<=',
                'MAIORIGUAL': '>='
            }
            temp = self.novo_temp()
            self.codigo_intermediario.append(f"{temp} := {esquerda['lugar']} {op_map[operador]} {direita['lugar']}")
            esquerda = { 'tipo': 'BOOL', 'lugar': temp }

        # Operadores lógicos (AND, OR)
        while self.pos < len(self.tokens) and self.token_atual().tipo in ('AND', 'OR'):
            operador = self.token_atual().tipo
            self.consumir(operador)

            direita = self.expressao_termo()

            if esquerda['tipo'] != 'BOOL' or direita['tipo'] != 'BOOL':
                self.erro(f"Operador lógico '{operador}' espera booleanos, mas recebeu {esquerda['tipo']} e {direita['tipo']}")

            op = '&&' if operador == 'AND' else '||'
            temp = self.novo_temp()
            self.codigo_intermediario.append(f"{temp} := {esquerda['lugar']} {op} {direita['lugar']}")
            esquerda = { 'tipo': 'BOOL', 'lugar': temp }

        return esquerda

    def expressao_or(self):
        self.expressao_and()
        while self.token_atual().tipo == 'OR':
            self.consumir('OR')
            self.expressao_and()

    def expressao_and(self):
        self.expressao_relacional()
        while self.token_atual().tipo == 'AND':
            self.consumir('AND')
            self.expressao_relacional()

    def expressao_relacional(self):
        self.expressao_soma()
        while self.token_atual().tipo in ('IGUAL', 'DIFERENTE', 'MENOR', 'MAIOR', 'MENORIGUAL', 'MAIORIGUAL'):
            self.consumir(self.token_atual().tipo)
            self.expressao_soma()

    def expressao_soma(self):
        self.expressao_termo()
        while self.token_atual().tipo in ('SOMA', 'SUB'):
            self.consumir(self.token_atual().tipo)
            self.expressao_termo()

    def expressao_termo(self):
        esquerda = self.expressao_fator()

        while self.pos < len(self.tokens) and self.token_atual().tipo in ('MULT', 'DIV'):
            operador = self.token_atual().tipo
            self.consumir(operador)

            direita = self.expressao_fator()

            if esquerda['tipo'] != 'INT' or direita['tipo'] != 'INT':
                self.erro(f"Operador '{operador}' espera inteiros, mas recebeu {esquerda['tipo']} e {direita['tipo']}")

            op = '*' if operador == 'MULT' else '/'
            temp = self.novo_temp()
            self.codigo_intermediario.append(f"{temp} := {esquerda['lugar']} {op} {direita['lugar']}")
            esquerda = { 'tipo': 'INT', 'lugar': temp }

        return esquerda


    def chamada_funcao_com_retorno(self):
        nome = self.token_atual().lexema
        simbolo = self.tabela.buscar(nome)

        if simbolo['categoria'] != 'funcao':
            raise Exception(f"Erro semântico: '{nome}' não é uma função.")

        self.consumir('ID')
        self.consumir('LPAREN')

        parametros_esperados = simbolo.get('parametros', [])
        argumentos_recebidos = []

        # self.avaliando_argumentos = True
        if self.token_atual().tipo != 'RPAREN':
            while True:
                valor = self.expressao()
                argumentos_recebidos.append(valor)
                if self.token_atual().tipo != 'VIRGULA':
                    break
                self.consumir('VIRGULA')
        # self.avaliando_argumentos = False

        self.consumir('RPAREN')  # <- ESSENCIAL AQUI!

        if len(argumentos_recebidos) != len(parametros_esperados):
            raise Exception(f"Erro semântico: função '{nome}' espera {len(parametros_esperados)} argumentos, mas recebeu {len(argumentos_recebidos)}.")

        for (param_nome, param_tipo), arg in zip(parametros_esperados, argumentos_recebidos):
            if param_tipo != arg['tipo']:
                raise Exception(f"Erro semântico: tipo de argumento incompatível. Esperado '{param_tipo}', mas recebeu '{arg['tipo']}'.")

            self.codigo_intermediario.append(f"param {arg['lugar']}")

        temp = self.novo_temp()
        self.codigo_intermediario.append(f"{temp} := call {nome}, {len(argumentos_recebidos)}")

        return { 'tipo': simbolo['retorno'], 'lugar': temp }


    def expressao_fator(self):
        token = self.token_atual()
        tipo = token.tipo
        lexema = token.lexema

        if tipo == 'ID':
            if not self.tabela.existe(lexema):
                self.erro(f"Variável '{lexema}' não declarada.")

            # if (not self.avaliando_argumentos
            #     and self.pos + 1 < len(self.tokens)
            #     and self.tokens[self.pos + 1].tipo == 'LPAREN'):
            #     return self.chamada_funcao_com_retorno()

            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].tipo == 'LPAREN':
                return self.chamada_funcao_com_retorno()


            simbolo = self.tabela.buscar(lexema)
            self.consumir('ID')
            return { 'tipo': simbolo['tipo'], 'lugar': lexema }

        elif tipo == 'NUMERO':
            self.consumir('NUMERO')
            return { 'tipo': 'INT', 'lugar': lexema }

        elif tipo == 'STRING_LITERAL':
            self.consumir('STRING_LITERAL')
            return { 'tipo': 'STRING', 'lugar': lexema }

        elif tipo in ('TRUE', 'FALSE'):
            self.consumir(tipo)
            return { 'tipo': 'BOOL', 'lugar': lexema }

        elif tipo == 'LPAREN':
            self.consumir('LPAREN')
            resultado = self.expressao()
            self.consumir('RPAREN')
            return resultado

        else:
            self.erro(f"Token inesperado na expressão: {tipo}")
            return { 'tipo': 'ERRO', 'lugar': '?' }




