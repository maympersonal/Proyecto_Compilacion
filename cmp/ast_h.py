import cmp.visitor as visitor
import inspect



class Node:
    def evaluate(self):
        raise NotImplementedError()

# Se usa en el parser en la regla inicial `program : program_decl_list`. 
# Se le pasa `program_decl_list`.
class Program(Node):
    def __init__(self, program_decl_list):
        super().__init__()
        self.program_decl_list = program_decl_list

    def print_visitor(self, visitor):
        decls = " , ".join([
            visitor.visit(pr) for pr in self.program_decl_list
        ]) if isinstance(self.program_decl_list, list) else visitor.visit(
            self.program_decl_list)
        return f'{self.__class__.__name__} ({decls})'


# Se usa en el parser en la regla `program_level_decl : function_declaration`.
# Se le pasa `identifier`, `body`, `type_anotation` y `parameters`.
class FunctionDeclaration(Node):

    def __init__(self, identifier, body, type_anotation = None, parameters=[]):
        super().__init__()
        self.identifier = identifier
        self.type_anotation = type_anotation
        self.parameters = parameters
        self.body = body
    
    def print_visitor(self, visitor):
        #type_anotation = visitor.visit(self.type_anotation)
        parameters = " , ".join([visitor.visit(pr) for pr in self.parameters])
        body = visitor.visit(self.body)
        return f'{self.__class__.__name__} ({self.identifier} {self.type_anotation} {parameters} {body})'




# Se usa en el parser en la regla `var_dec : LET var_init_list IN var_decl_expr`.
# Se le pasa `var_init_list` y `body`.
class VarDeclaration(Node):

    def __init__(self, var_init_list, body):
        super().__init__()
        self.var_init_list = var_init_list
        self.body = body

    def print_visitor(self, visitor):
        var_init_list = " , ".join(
            [visitor.visit(pr) for pr in self.var_init_list])
        body = visitor.visit(self.body)
        return f'{self.__class__.__name__} ({var_init_list} {body})'


# Se usa en el parser en la regla `var_init : identifier ASSIGN inst` 
# o `var_init : identifier ASSIGN inst type_downcast`.
# Se le pasa `identifier`, `expression` y `type_downcast`.
class VarInit(Node):

    def __init__(self, identifier, expression, type_downcast=None):
        super().__init__()
        self.identifier = identifier
        self.expression = expression
        self.type_downcast = type_downcast

    def print_visitor(self, visitor):
        identifier = visitor.visit(self.identifier)
        expression = visitor.visit(self.expression)
        type_downcast = visitor.visit(self.type_downcast) if self.type_downcast!=None else self.type_downcast
        return f'{self.__class__.__name__} ({identifier} {expression} {type_downcast})'

# Se usa en el parser en la regla `atribute_declaration : identifier ASSIGN expression` 
# o `atribute_declaration : identifier ASSIGN expression type_downcast`.
# Se le pasa `identifier`, `expression` y `type_downcast`.
class TypeVarInit(VarInit):
    pass

# Se usa en el parser en la regla `identifier : atom` 
# o `identifier : fully_typed_param`.
# Se le pasa `identifier` y `type`.
class VarUse(Node):

    def __init__(self, identifier, type=None):
        super().__init__()
        self.type = type
        self.identifier = identifier

    def print_visitor(self, visitor):
        identifier = self.identifier if isinstance(self.identifier, str) else visitor.visit(self.identifier)
        return f'{self.__class__.__name__} ({identifier} {self.type})'

# Se usa en el parser en la regla `VectorVarUse : identifier LBRACKET expression RBRACKET`.
# Se le pasa `identifier` e `index`.
class VectorVarUse(Node):

    def __init__(self, identifier, index):
        super().__init__()
        self.index = index
        self.identifier = identifier

    def print_visitor(self, visitor):
        index = visitor.visit(self.index)
        identifier = self.identifier if isinstance(self.identifier, str) else visitor.visit(self.identifier)
        return f'{self.__class__.__name__} ({identifier} {index})'

# Se usa en el parser en la regla `InlineConditional : conditional_expression 
# LPAREN conditional_expression RPAREN expression else_elif_statement.
# Se le pasa `conditional_expression`, `expression` y `else_elif_statement`.
class InlineConditional(Node):

    def __init__(self, conditional_expression, expression,
                 else_elif_statement):
        self.conditional_expression = conditional_expression
        self.expression = expression
        self.else_elif_statement = else_elif_statement

    def print_visitor(self, visitor):
        conditional_expression = visitor.visit(self.conditional_expression)
        true_branch = visitor.visit(self.expression)
        false_branch = visitor.visit(self.else_elif_statement)
        return f'{self.__class__.__name__} ({conditional_expression} {true_branch} {false_branch})'

# Se usa en el parser en la regla `FullConditional : conditional_expression 
# scope_list else_elif_statement`.
# Se le pasa `conditional_expression`, `scope_list` y `else_elif_statement`.
class FullConditional(Node):

    def __init__(self, conditional_expression, scope_list,
                 else_elif_statement):
        self.conditional_expression = conditional_expression
        self.scope_list = scope_list
        self.else_elif_statement = else_elif_statement

    def print_visitor(self, visitor):
        conditional_expression = visitor.visit(self.conditional_expression)
        scope_list = " , ".join([visitor.visit(pr) for pr in self.scope_list])
        else_elif_statement = visitor.visit(self.else_elif_statement)
        return f'{self.__class__.__name__} ({conditional_expression} {scope_list} {else_elif_statement})'

# Se usa en el parser en la regla `flux_control : WHILE expression DO inst_list END`.
# Se le pasa `condition` y `body`.
class WhileLoop(Node):

    def __init__(self, condition, body):
        super().__init__()
        self.condition = condition
        self.body = body

    def print_visitor(self, visitor):
        condition = visitor.visit(self.condition)
        body = visitor.visit(self.body)
        return f'{self.__class__.__name__} ({condition} {body})'

# Se usa en el parser en la regla `flux_control : FOR identifier IN expression DO inst_list END`.
# Se le pasa `identifier`, `expression` y `body`.
class ForLoop(Node):

    def __init__(self, identifier, expression, body):
        super().__init__()
        self.identifier = identifier
        self.expression = expression
        self.body = body

    def print_visitor(self, visitor):
        identifier = visitor.visit(self.identifier)
        expression = visitor.visit(self.expression)
        body = visitor.visit(self.body)
        return f'{self.__class__.__name__} ({identifier} {expression} {body})'

# Se usa en el parser en la regla `expression : identifier LPAREN argument_list RPAREN`.
# Se le pasa `identifier` y `arguments`.
class FunctionCall(Node):

    def __init__(self, identifier, arguments=[]):
        super().__init__()
        self.identifier = identifier
        self.arguments = arguments

    def print_visitor(self, visitor):
        arguments = " , ".join([visitor.visit(pr) for pr in self.arguments])
        return f'{self.__class__.__name__} ({self.identifier} {arguments})'

# Se usa en el parser en la regla `scope : LBRACE inst_list RBRACE` y `scope : LBRACE RBRACE`.
# Se le pasa `statements`.
class Scope(Node):

    def __init__(self, statements):
        super().__init__()
        self.statements = statements
        print(self.statements)

    def print_visitor(self, visitor):
        statements = [visitor.visit(st) for st in self.statements]
        return f'{self.__class__.__name__} ({" , ".join(statements)})'

# Se usa en el parser en la regla `scope_list : scope` y `scope_list : scope scope_list`.
# Se le pasa `scopes`.
class ScopeList(Node):

    def __init__(self, scopes):
        super().__init__()
        self.scopes = scopes

    def print_visitor(self, visitor):
        scopes = [visitor.visit(sc) for sc in self.scopes]
        return f'{self.__class__.__name__} ({scopes})'



# Se usa en el parser en las reglas `inst_list : inst`, `inst_list : inst SEMICOLON`, y `inst_list : inst SEMICOLON inst_list`.
# No se le pasan parámetros en su inicialización.
class Instruction(Node):

    def print_visitor(self, visitor):
        return f'{self.__class__.__name__} ({self})'


# Se usa en el parser en las reglas `inst : expression` y `var_decl_expr : expression`.
# No se le pasan parámetros en su inicialización.
class Expression(Instruction):

    def print_visitor(self, visitor):
        return f'{self.__class__.__name__} ({self})'


# Se usa en el parser en la regla `aritmetic_operation : term aritmetic_operation`.
# Parámetros que se le pasan a la clase:
# - term: el término de la operación aritmética.
# - aritmetic_operation: la operación aritmética que se aplica al término.
class Aritmetic_operation(Expression):
    def __init__(self, term, aritmetic_operation):
        super().__init__()
        self.term = term
        self.aritmetic_operation = aritmetic_operation

    def print_visitor(self, visitor):
        return f'{self.__class__.__name__} ({self})'

# Se usa en el parser en la regla `expression : atom CONCAT expression` o `expression : atom ESPACEDCONCAT expression`.
# Parámetros que se le pasan a la clase:
# - operation: la operación de concatenación (puede ser CONCAT o ESPACEDCONCAT).
# - atom: el átomo que se concatena.
# - expression: la expresión con la que se concatena el átomo.
class Concat(Expression):

    def __init__(self, operation, atom, expression):
        super().__init__()
        self.operation = operation
        self.atom = atom
        self.expression = expression

    def print_visitor(self, visitor):
        atom = visitor.visit(self.atom)
        expression = visitor.visit(self.expression)
        return f'{self.__class__.__name__} ({atom} {self.operation} {expression})'

# Se usa en el parser en la regla `aritmetic_operation : aritmetic_operation PLUS term`.
# Parámetros que se le pasan a la clase:
# - term: el término que se está sumando.
# - aritmetic_operation: la operación aritmética anterior (si existe).
class Add(Aritmetic_operation):

    def print_visitor(self, visitor):
        term = visitor.visit(self.term)
        arith_op = visitor.visit(self.aritmetic_operation)
        return f'{self.__class__.__name__} ({term} {arith_op})'

# Se usa en el parser en la regla `aritmetic_operation : term MINUS aritmetic_operation`.
# Parámetros que se le pasan a la clase:
# - term: el término del cual se está restando.
# - aritmetic_operation: la operación aritmética anterior (si existe).
class Sub(Aritmetic_operation):

    def print_visitor(self, visitor):
        term = visitor.visit(self.term)
        arith_op = visitor.visit(self.aritmetic_operation)
        return f'{self.__class__.__name__} ({term} {arith_op})'

# Se usa en el parser en la regla `term : factor MULTIPLY term`, `term : factor DIVIDE term`, `term : factor MODULE term`, y `term : factor`.
# Parámetros que se le pasan a la clase:
# - factor: el factor que se multiplica, divide o toma módulo.
# - term: el término con el cual se realiza la operación.
class Term(Node):

    def __init__(self, factor, term):
        super().__init__()
        self.factor = factor
        self.term = term

# Se usa en el parser en la regla `term : factor MODULE term`.
# Parámetros que se le pasan a la clase:
# - factor: el factor sobre el cual se aplica el módulo.
# - term: el término que representa el módulo.
class Mod(Term):

    def print_visitor(self, visitor):
        factor = visitor.visit(self.factor)
        term = visitor.visit(self.term) if self.term else ''
        return f'{self.__class__.__name__} ({factor} {term})'

# Se usa en el parser en la regla `term : factor DIVIDE term`.
# Parámetros que se le pasan a la clase:
# - factor: el factor sobre el cual se aplica la división.
# - term: el término que representa el divisor.
class Div(Term):

    def print_visitor(self, visitor):
        factor = visitor.visit(self.factor)
        term = visitor.visit(self.term) if self.term else ''
        return f'{self.__class__.__name__} ({factor} {term})'

# Se usa en el parser en la regla `term : factor MULTIPLY term`.
# Parámetros que se le pasan a la clase:
# - factor: el factor que se multiplica.
# - term: el término que representa el multiplicador.
class Mult(Term):

    def print_visitor(self, visitor):
        factor = visitor.visit(self.factor)
        term = visitor.visit(self.term) if self.term else ''
        return f'{self.__class__.__name__} ({factor} {term})'

# Se usa en el parser en las reglas `factor : factor POWER base_exponent` y `factor : factor ASTERPOWER base_exponent`.
# Parámetros que se le pasan a la clase:
# - base_exponent: representa la base y el exponente de la operación.
class Factor(Node):

    def __init__(self, base_exponent):
        super().__init__()
        self.base_exponent = base_exponent

# Se usa en el parser en las reglas `factor : factor POWER base_exponent` y `factor : factor ASTERPOWER base_exponent`.
# Parámetros que se le pasan a la clase:
# - factor: representa el factor sobre el cual se aplica la potencia.
# - base_exponent: representa la base y el exponente de la operación.
class Power(Factor):

    def __init__(self, factor, base_exponent):
        super().__init__(base_exponent)
        self.factor = factor

    def print_visitor(self, visitor):
        factor = visitor.visit(self.factor)
        base_exponent = visitor.visit(self.base_exponent)
        return f'{self.__class__.__name__} ({factor} {base_exponent})'



# Se usa en el parser en varias reglas donde se necesita un átomo como parte de una expresión.
# Parámetros que se le pasan a la clase:
# - value: representa el valor del átomo, que puede ser un identificador, número, cadena, etc.
class Atom(Node):

    def __init__(self, value):
        super().__init__()
        self.value = value

# Se usa en el parser cuando se necesita representar una cadena como un átomo en una expresión.
# Parámetros que se le pasan a la clase:
# - value: representa el valor de la cadena.
class String(Atom):

    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def print_visitor(self, visitor):
        return f'{self.__class__.__name__} ("{self.value}")'

# Se usa en el parser cuando se necesita representar un número como un átomo en una expresión.
# Parámetros que se le pasan a la clase:
# - value: representa el valor numérico.
class Number(Atom):

    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def print_visitor(self, visitor):
        return f'{self.__class__.__name__} ({self.value})'

# Se usa en el parser cuando se necesita representar un booleano como un átomo en una expresión.
# Parámetros que se le pasan a la clase:
# - value: representa el valor booleano (True o False).
class Boolean(Atom):

    def __init__(self, value):
        super().__init__(value)
        self.value = value

    def print_visitor(self, visitor):
        return f'{self.__class__.__name__} ({self.value})'

# Se usa en el parser para representar operaciones unarias en una expresión matemática.
# Parámetros que se le pasan a la clase:
# - sign: representa el signo de la operación unaria ('+' o '-').
# - factor: representa el factor sobre el cual se aplica la operación unaria.
class Unary(Factor):
    def __init__(self, sign, factor):
        super().__init__()
        self.sign = sign
        self.factor = factor
    
    def print_visitor(self, visitor):
        factor = visitor.visit(self.factor)
        return f'{self.__class__.__name__} ({self.sign} {factor})'

# Se usa en el parser para representar funciones internas unarias.
# Parámetros que se le pasan a la clase:
# - func: representa la función interna que se está aplicando.
# - argument: representa el argumento sobre el cual se aplica la función interna.
class UnaryBuildInFunction(Atom):

    def __init__(self, func, argument):
        super().__init__(argument)
        self.func = func
        self.argument = argument

    def print_visitor(self, visitor):
        argument = visitor.visit(self.argument)
        return f'{self.__class__.__name__} ({self.func} {argument})'

# Se usa en el parser para representar funciones internas binarias.
# Parámetros que se le pasan a la clase:
# - func: representa la función interna que se está aplicando.
# - argument1: primer argumento de la función.
# - argument2: segundo argumento de la función.
class BinaryBuildInFunction(Atom):

    def __init__(self, func, argument1, argument2):
        self.func = func
        self.argument1 = argument1
        self.argument2 = argument2

    def print_visitor(self, visitor):
        argument1 = visitor.visit(self.argument1)
        argument2 = visitor.visit(self.argument2)
        return f'{self.__class__.__name__} ({self.func} {argument1} {argument2})'

# Se usa en el parser para representar funciones internas sin parámetros.
# Parámetros que se le pasan a la clase:
# - func: representa la función interna que se está aplicando.
class NoParamBuildInFunction(Atom):

    def __init__(self, func):
        self.func = func

    
    def print_visitor(self, visitor):

        return f'{self.__class__.__name__} ({self.func})'

# Se usa en el parser para representar constantes internas.
# Parámetros que se le pasan a la clase:
# - const: representa la constante interna que se está utilizando.
class BuildInConst(Atom):

    def __init__(self, const):
        super().__init__(const)
        self.const = const

    def print_visitor(self, visitor):
        return f'{self.__class__.__name__} ({self.const})'

# Se usa en el parser para representar expresiones condicionales.
# No tiene parámetros específicos adicionales en su inicialización.
class Conditional_Expression(Node):
    pass

# Se usa en el parser para representar operaciones de negación lógica.
# Parámetros:
# - condition: representa la condición que se está negando.
class Not(Conditional_Expression):

    def __init__(self, condition):
        super().__init__()
        self.condition = condition

    def print_visitor(self, visitor):
        condition = visitor.visit(self.condition)
        return f'{self.__class__.__name__} ({condition})'

# Se usa en el parser para representar operaciones lógicas de "or" (o).
# Parámetros:
# - condition: la primera condición en la operación "or".
# - conditional_expression: la segunda condición en la operación "or".
class Or(Conditional_Expression):

    def __init__(self, condition, conditional_expression):
        super().__init__()
        self.condition = condition
        self.conditional_expression = conditional_expression

    def print_visitor(self, visitor):
        condition = visitor.visit(self.condition)
        conditional_expression = visitor.visit(self.conditional_expression)
        return f'{self.__class__.__name__} ({condition} {conditional_expression})'

# Se usa en el parser para representar operaciones lógicas de "and" (y).
# Parámetros:
# - condition: la primera condición en la operación "and".
# - conditional_expression: la segunda condición en la operación "and".
class And(Conditional_Expression):

    def __init__(self, condition, conditional_expression):
        super().__init__()
        self.condition = condition
        self.conditional_expression = conditional_expression

    def print_visitor(self, visitor):
        condition = visitor.visit(self.condition)
        conditional_expression = visitor.visit(self.conditional_expression)
        return f'{self.__class__.__name__} ({condition} {conditional_expression})'

# Se usa en el parser para representar la condición "is".
# Parámetros:
# - condition: la condición principal o variable a verificar.
# - conditional_expression: la expresión o valor con el que se compara la condición.
class Is(Conditional_Expression):

    def __init__(self, condition, conditional_expression):
        super().__init__()
        self.condition = condition
        self.conditional_expression = conditional_expression

    def print_visitor(self, visitor):
        conditional_expression = visitor.visit(self.conditional_expression)
        return f'{self.__class__.__name__} ({self.condition} {conditional_expression})'

# Representa una comparación entre dos expresiones.
# Parámetros:
# - expr1: primera expresión en la comparación.
# - expr2: segunda expresión en la comparación.
class Comparation(Node):

    def __init__(self, expr1, expr2):
        super().__init__()
        self.expr1 = expr1
        self.expr2 = expr2

    def print_visitor(self, visitor):
        argument1 = visitor.visit(self.expr1)
        argument2 = visitor.visit(self.expr2)
        return f'({argument1} {argument2})'

class Not_Equal(Comparation):
    def print_visitor(self, visitor):
        expr1 = visitor.visit(self.expr1)
        expr2 = visitor.visit(self.expr2)
        return f'{self.__class__.__name__} ({expr1} {expr2})'

# Representa una operación de desigualdad entre dos expresiones.
class NotEqual(Comparation):

    def __init__(self, expr1, expr2):
        super().__init__(expr1, expr2)

# Representa una operación de igualdad entre dos expresiones.
class Equal(Comparation):

    def __init__(self, expr1, expr2):
        super().__init__(expr1, expr2)

# Representa una operación de comparación "menor o igual que" entre dos expresiones.
class LessEqual(Comparation):

    def __init__(self, expr1, expr2):
        super().__init__(expr1, expr2)

# Representa una operación de comparación "mayor o igual que" entre dos expresiones.
class GreaterEqual(Comparation):

    def __init__(self, expr1, expr2):
        super().__init__(expr1, expr2)

# Representa una operación de comparación "menor que" entre dos expresiones.
class LessThan(Comparation):

    def __init__(self, expr1, expr2):
        super().__init__(expr1, expr2)

# Representa una operación de comparación "mayor que" entre dos expresiones.
class GreaterThan(Comparation):

    def __init__(self, expr1, expr2):
        super().__init__(expr1, expr2)

# Nodo utilizado en el parser para representar llamadas a métodos de objetos.
# Se usa en contextos donde se espera que un objeto (`identifier`) llame a un método (`function_call`).

class VarMethod(Node):

    def __init__(self, identifier, function_call):
        super().__init__()
        self.identifier = identifier
        self.function_call = function_call

    def print_visitor(self, visitor):
        function_call = visitor.visit(self.function_call)
        return f'{self.__class__.__name__} ({self.identifier} {function_call})'

# Nodo utilizado en el parser para representar acceso a atributos de variables u objetos.
# Se usa en contextos donde se espera que se acceda a un atributo (`attr`) de una variable u objeto (`identifier`).
class VarAttr(Node):

    def __init__(self, identifier, attr):
        super().__init__()
        self.identifier = identifier
        self.attr = attr

    def print_visitor(self, visitor):
        attr = self.attr if isinstance(self.attr, str) else visitor.visit(self.attr)
        return f'{self.__class__.__name__} ({self.identifier} {attr})'

# Nodo utilizado en el parser para representar la declaración de tipos.
# Se usa para declarar un tipo con un identificador (`identifier`), parámetros opcionales (`parameters`),
# un tipo heredado (`inherits_type`) y un cuerpo de declaración (`decl_body`).
class TypeDeclaration(Node):
    def __init__(self, identifier, parameters=None, inherits_type=None, decl_body=None):
        super().__init__()
        self.identifier = identifier
        self.parameters = parameters
        self.inherits_type = inherits_type
        self.decl_body = decl_body

    def print_visitor(self, visitor):
        parameters = [visitor.visit(pr) for pr in self.parameters] if self.parameters != None else None
        inherits_type = visitor.visit(self.inherits_type) if self.inherits_type != None else None
        decl_body = visitor.visit(self.decl_body)

        return f'{self.__class__.__name__} ({self.identifier} {parameters} {inherits_type} {decl_body})'

# Nodo utilizado en el parser para representar la especificación de tipos de herencia.
# Se usa para especificar el identificador del tipo base (`identifier`) y los parámetros opcionales (`parameters`).
class InheritsType(Node):
    def __init__(self, identifier, parameters=None):
        super().__init__()
        self.identifier = identifier
        self.parameters = parameters
        
    def print_visitor(self, visitor):
       parameters = [visitor.visit(pr) for pr in self.parameters] if self.parameters != None else None
       return f'{self.__class__.__name__} ({self.identifier}, {parameters})'

# Nodo utilizado en el parser para representar la instanciación de tipos.
# Se usa para representar una instancia del tipo `identifier` con los `arguments` proporcionados.
class TypeInstanciation(Node):
    def __init__(self, identifier, arguments = []):
        super().__init__()
        self.identifier = identifier
        self.arguments = arguments
    
    def print_visitor(self, visitor):
       arguments = [visitor.visit(ar) for ar in self.arguments]
       return f'{self.__class__.__name__} ({self.identifier}, {arguments})'

# Nodo utilizado en el parser para representar el ámbito de declaración.
# Se usa para agrupar declaraciones y sentencias dentro de un ámbito específico.
class DeclarationScope(Node):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements
    
    def print_visitor(self, visitor):
        statements = [visitor.visit(st) for st in self.statements]
        return f'{self.__class__.__name__} ({" , ".join(statements)})'

# Nodo utilizado en el parser para representar la declaración de un método.
# Se utiliza para definir la estructura de un método dentro de una clase o módulo.       
class TypeMethodDeclaration(Node):
    def __init__(self, identifier, body, type_anotation = None, parameters=[]):
        super().__init__()
        self.identifier = identifier
        self.type_anotation = type_anotation
        self.parameters = parameters
        self.body = body
    
    def print_visitor(self, visitor):
        parameters = " , ".join([visitor.visit(pr) for pr in self.parameters])
        body = visitor.visit(self.body)
        return f'{self.__class__.__name__} ({self.identifier} {self.type_anotation} {parameters} {body})'

# Nodo utilizado en el parser para representar la declaración de un protocolo.
# Se utiliza para definir la estructura de un protocolo en el lenguaje.
class ProtocolDeclaration(Node):
    def __init__(self, name, body, extends =None):
        super().__init__()
        self.name = name
        self.extends = extends
        self.body = body
        
    def print_visitor(self, visitor):
        body = " , ".join([visitor.visit(pr) for pr in self.body])
        return f'{self.__class__.__name__} ({self.name} {self.extends} {body})'

# Node used in the parser to represent a virtual method declaration.
# It is used to define the structure of a virtual method in the language.
class ProtocolMethodDeclaration(Node):
    def __init__(self, method_name, type_annotation, parameters=None):
        super().__init__()
        self.method_name = method_name
        self.parameters = parameters
        self.type_annotation = type_annotation

    def print_visitor(self, visitor):
        parameters = None if self.parameters == None else " , ".join([visitor.visit(pr) for pr in self.parameters])
        return f'{self.__class__.__name__} ({self.method_name} {self.type_annotation} {parameters})'

# Representa un nodo de declaración de rango de vector en el analizador sintáctico.
# Encapsula toda la declaración de rango para vectores.
class VectorRangeDeclaration(Node):

    def __init__(self, range):
        super().__init__()
        self.range = range

    def print_visitor(self, visitor):
        range = " , ".join(
            [visitor.visit(pr) for pr in self.range])
        return f'{self.__class__.__name__} ({range})'

# Representa un nodo de declaración de expresión de vector en el analizador sintáctico.
# Encapsula la declaración de una expresión de vector con su identificador y expresión de rango.
class VectorExpressionDeclaration(Node):

    def __init__(self, expression, identifier, rangeexpression):
        super().__init__()
        self.expression = expression
        self.identifier = identifier
        self.rangeexpression = rangeexpression

    def print_visitor(self, visitor):
        expression = visitor.visit(self.expression)
        identifier = visitor.visit(self.identifier)
        rangeexpression = visitor.visit(self.rangeexpression)
        return f'{self.__class__.__name__} ({expression} {identifier} { rangeexpression})'

class HulkPrintVisitor(object):
    
    tabs = -1

    def __init__(self):
        super().__init__()

    @visitor.on('node')
    def visit(self, node, tabs):
        pass

    @visitor.when(Node)
    def visit(self, node):
        self.tabs = self.tabs + 1 
        inter = '\\__ ' if self.tabs > 0 else ''
        result = '\n' + '\t' * self.tabs + inter + node.print_visitor(self)
        self.tabs = self.tabs - 1
        return result

