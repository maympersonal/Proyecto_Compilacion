from Lexer.Cmp_lex.pycompiler import Production, Sentence, Symbol, EOF, Epsilon
from typing import Tuple
class LexerError(Exception):
    def __init__(self, message):
        super().__init__(message)

class ContainerSet:
    def __init__(self, *values, contains_epsilon=False):
        self.set = set(values)
        self.contains_epsilon = contains_epsilon

    def add(self, value):
        n = len(self.set)
        self.set.add(value)
        return n != len(self.set)

    def extend(self, values):
        change = False
        for value in values:
            change |= self.add(value)
        return change

    def set_epsilon(self, value=True):
        last = self.contains_epsilon
        self.contains_epsilon = value
        return last != self.contains_epsilon

    def update(self, other):
        n = len(self.set)
        self.set.update(other.set)
        return n != len(self.set)

    def epsilon_update(self, other):
        return self.set_epsilon(self.contains_epsilon | other.contains_epsilon)

    def hard_update(self, other):
        return self.update(other) | self.epsilon_update(other)

    def find_match(self, match):
        for item in self.set:
            if item == match:
                return item
        return None

    def __len__(self):
        return len(self.set) + int(self.contains_epsilon)

    def __str__(self):
        return '%s-%s' % (str(self.set), self.contains_epsilon)

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.set)

    def __nonzero__(self):
        return len(self) > 0

    def __eq__(self, other):
        if isinstance(other, set):
            return self.set == other
        return isinstance(other, ContainerSet) and self.set == other.set and self.contains_epsilon == other.contains_epsilon


def inspect(item, grammar_name='G', mapper=None):
    try:
        return mapper[item]
    except (TypeError, KeyError ):
        if isinstance(item, dict):
            items = ',\n   '.join(f'{inspect(key, grammar_name, mapper)}: {inspect(value, grammar_name, mapper)}' for key, value in item.items() )
            return f'{{\n   {items} \n}}'
        elif isinstance(item, ContainerSet):
            args = f'{ ", ".join(inspect(x, grammar_name, mapper) for x in item.set) } ,' if item.set else ''
            return f'ContainerSet({args} contains_epsilon={item.contains_epsilon})'
        elif isinstance(item, EOF):
            return f'{grammar_name}.EOF'
        elif isinstance(item, Epsilon):
            return f'{grammar_name}.Epsilon'
        elif isinstance(item, Symbol):
            return f"G['{item.Name}']"
        elif isinstance(item, Sentence):
            items = ', '.join(inspect(s, grammar_name, mapper) for s in item._symbols)
            return f'Sentence({items})'
        elif isinstance(item, Production):
            left = inspect(item.Left, grammar_name, mapper)
            right = inspect(item.Right, grammar_name, mapper)
            return f'Production({left}, {right})'
        elif isinstance(item, tuple) or isinstance(item, list):
            ctor = ('(', ')') if isinstance(item, tuple) else ('[',']')
            return f'{ctor[0]} {("%s, " * len(item)) % tuple(inspect(x, grammar_name, mapper) for x in item)}{ctor[1]}'
        else:
            raise ValueError(f'Invalid: {item}')

def pprint(item, header=""):
    if header:
        print(header)

    if isinstance(item, dict):
        for key, value in item.items():
            print(f'{key}  --->  {value}')
    elif isinstance(item, list):
        print('[')
        for x in item:
            print(f'   {repr(x)}')
        print(']')
    else:
        print(item)

# class Token:
#     """
#     Basic token class.

#     Parameters
#     ----------
#     lex : str
#         Token's lexeme.
#     token_type : Enum
#         Token's type.
#     """

#     def __init__(self, lex, token_type, pos):
#         self.lex = lex
#         self.token_type = token_type
#         self.pos = pos

#     def __str__(self):
#         return f'{self.token_type}: {self.lex}. Position: {self.pos}'

#     def __repr__(self):
#         return str(self)

#     @property
#     def is_valid(self):
#         return True
class Token(object):
    '''
    Representation of a single token.
    '''
    def __init__(self, value, type, pos: Tuple[int,int]):
        self.type = type
        self.value = value
        self.lineno = pos[0]
        self.index = pos[1]
    __slots__ = ('type', 'value', 'lineno', 'index', 'end')
    def __repr__(self):
        return f'Token(type={self.type!r}, value={self.value!r}, lineno={self.lineno}, index={self.index})'


class UnknownToken(Token):
    def __init__(self, lex):
        Token.__init__(self, lex, None)

    def transform_to(self, token_type):
        return Token(self.lex, token_type)

    @property
    def is_valid(self):
        return False

def tokenizer(G, fixed_tokens):
    def decorate(func):
        def tokenize_text(text):
            tokens = []
            for lex in text.split():
                try:
                    token = fixed_tokens[lex]
                except KeyError:
                    token = UnknownToken(lex)
                    try:
                        token = func(token)
                    except TypeError:
                        pass
                tokens.append(token)
            tokens.append(Token('$', G.EOF))
            return tokens

        if hasattr(func, '__call__'):
            return tokenize_text
        elif isinstance(func, str):
            return tokenize_text(func)
        else:
            raise TypeError('Argument must be "str" or a callable object.')
    return decorate

class DisjointSet:
    def __init__(self, *items):
        self.nodes = { x: DisjointNode(x) for x in items }

    def merge(self, items):
        items = (self.nodes[x] for x in items)
        try:
            head, *others = items
            for other in others:
                head.merge(other)
        except ValueError:
            pass

    @property
    def representatives(self):
        return { n.representative for n in self.nodes.values() }

    @property
    def groups(self):
        return [[n for n in self.nodes.values() if n.representative == r] for r in self.representatives]

    def __len__(self):
        return len(self.representatives)

    def __getitem__(self, item):
        return self.nodes[item]

    def __str__(self):
        return str(self.groups)

    def __repr__(self):
        return str(self)

class DisjointNode:
    def __init__(self, value):
        self.value = value
        self.parent = self

    @property
    def representative(self):
        if self.parent != self:
            self.parent = self.parent.representative
        return self.parent

    def merge(self, other):
        other.representative.parent = self.representative

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return str(self)
    
import json

class Symbol(object):

    def __init__(self, name, grammar):
        self.Name = name
        self.Grammar = grammar

    def __str__(self):
        return self.Name

    def __repr__(self):
        return repr(self.Name)

    def __add__(self, other):
        if isinstance(other, Symbol):
            return Sentence(self, other)

        raise TypeError(other)

    def __or__(self, other):

        if isinstance(other, (Sentence)):
            return SentenceList(Sentence(self), other)

        raise TypeError(other)

    @property
    def IsEpsilon(self):
        return False

    def __len__(self):
        return 1

class NonTerminal(Symbol):


    def __init__(self, name, grammar):
        super().__init__(name, grammar)
        self.productions = []


    def __imod__(self, other):

        if isinstance(other, (Sentence)):
            p = Production(self, other)
            self.Grammar.Add_Production(p)
            return self

        if isinstance(other, tuple):
            assert len(other) > 1

            if len(other) == 2:
                other += (None,) * len(other[0])

            assert len(other) == len(other[0]) + 2, "Debe definirse una, y solo una, regla por cada símbolo de la producción"
            # assert len(other) == 2, "Tiene que ser una Tupla de 2 elementos (sentence, attribute)"

            if isinstance(other[0], Symbol) or isinstance(other[0], Sentence):
                p = AttributeProduction(self, other[0], other[1:])
            else:
                raise Exception("")

            self.Grammar.Add_Production(p)
            return self

        if isinstance(other, Symbol):
            p = Production(self, Sentence(other))
            self.Grammar.Add_Production(p)
            return self

        if isinstance(other, SentenceList):

            for s in other:
                p = Production(self, s)
                self.Grammar.Add_Production(p)

            return self

        raise TypeError(other)

    @property
    def IsTerminal(self):
        return False

    @property
    def IsNonTerminal(self):
        return True

    @property
    def IsEpsilon(self):
        return False

class Terminal(Symbol):

    def __init__(self, name, grammar):
        super().__init__(name, grammar)

    @property
    def IsTerminal(self):
        return True

    @property
    def IsNonTerminal(self):
        return False

    @property
    def IsEpsilon(self):
        return False

class EOF(Terminal):

    def __init__(self, Grammar):
        super().__init__('$', Grammar)

class Sentence(object):

    def __init__(self, *args):
        self._symbols = tuple(x for x in args if not x.IsEpsilon)
        self.hash = hash(self._symbols)

    def __len__(self):
        return len(self._symbols)

    def __add__(self, other):
        if isinstance(other, Symbol):
            return Sentence(*(self._symbols + (other,)))

        if isinstance(other, Sentence):
            return Sentence(*(self._symbols + other._symbols))

        raise TypeError(other)

    def __or__(self, other):
        if isinstance(other, Sentence):
            return SentenceList(self, other)

        if isinstance(other, Symbol):
            return SentenceList(self, Sentence(other))

        raise TypeError(other)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return ("%s " * len(self._symbols) % tuple(self._symbols)).strip()

    def __iter__(self):
        return iter(self._symbols)

    def __getitem__(self, index):
        return self._symbols[index]

    def __eq__(self, other):
        return self._symbols == other._symbols

    def __hash__(self):
        return self.hash

    @property
    def IsEpsilon(self):
        return False

class SentenceList(object):

    def __init__(self, *args):
        self._sentences = list(args)

    def Add(self, symbol):
        if not symbol and (symbol is None or not symbol.IsEpsilon):
            raise ValueError(symbol)

        self._sentences.append(symbol)

    def __iter__(self):
        return iter(self._sentences)

    def __or__(self, other):
        if isinstance(other, Sentence):
            self.Add(other)
            return self

        if isinstance(other, Symbol):
            return self | Sentence(other)


class Epsilon(Terminal, Sentence):

    def __init__(self, grammar):
        super().__init__('epsilon', grammar)


    def __str__(self):
        return "e"

    def __repr__(self):
        return 'epsilon'

    def __iter__(self):
        yield from ()

    def __len__(self):
        return 0

    def __add__(self, other):
        return other

    def __eq__(self, other):
        return isinstance(other, (Epsilon,))

    def __hash__(self):
        return hash("")

    @property
    def IsEpsilon(self):
        return True

class Production(object):

    def __init__(self, nonTerminal, sentence):

        self.Left = nonTerminal
        self.Right = sentence

    def __str__(self):

        return '%s := %s' % (self.Left, self.Right)

    def __repr__(self):
        return '%s -> %s' % (self.Left, self.Right)

    def __iter__(self):
        yield self.Left
        yield self.Right

    def __eq__(self, other):
        return isinstance(other, Production) and self.Left == other.Left and self.Right == other.Right

    def __hash__(self):
        return hash((self.Left, self.Right))

    @property
    def IsEpsilon(self):
        return self.Right.IsEpsilon

class AttributeProduction(Production):

    def __init__(self, nonTerminal, sentence, attributes):
        if not isinstance(sentence, Sentence) and isinstance(sentence, Symbol):
            sentence = Sentence(sentence)
        super(AttributeProduction, self).__init__(nonTerminal, sentence)

        self.attributes = attributes

    def __str__(self):
        return '%s := %s' % (self.Left, self.Right)

    def __repr__(self):
        return '%s -> %s' % (self.Left, self.Right)

    def __iter__(self):
        yield self.Left
        yield self.Right


    @property
    def IsEpsilon(self):
        return self.Right.IsEpsilon

    # sintetizar en ingles??????, pending aggrement
    def syntetice(self):
        pass

class Grammar():

    def __init__(self):

        self.Productions = []
        self.nonTerminals = []
        self.terminals = []
        self.startSymbol = None
        # production type
        self.pType = None
        self.Epsilon = Epsilon(self)
        self.EOF = EOF(self)

        self.symbDict = {'$': self.EOF}

    def addWhitespace(self):
        term = Terminal(' ', self)
        self.terminals.append(term)
        self.symbDict[' '] = term
        return term

    def NonTerminal(self, name, startSymbol=False):

        name = name.strip()
        if not name:
            raise Exception("Empty name")

        term = NonTerminal(name, self)

        if startSymbol:

            if self.startSymbol is None:
                self.startSymbol = term
            else:
                raise Exception("Cannot define more than one start symbol.")

        self.nonTerminals.append(term)
        self.symbDict[name] = term
        return term

    def NonTerminals(self, names):

        ans = tuple((self.NonTerminal(x) for x in names.strip().split()))

        return ans

    def Add_Production(self, production):

        if len(self.Productions) == 0:
            self.pType = type(production)

        assert type(production) == self.pType, "The Productions most be of only 1 type."

        production.Left.productions.append(production)
        self.Productions.append(production)

    def Terminal(self, name):

        name = name.strip()
        if not name:
            raise Exception("Empty name")

        term = Terminal(name, self)
        self.terminals.append(term)
        self.symbDict[name] = term
        return term

    def Terminals(self, names):

        ans = tuple((self.Terminal(x) for x in names.strip().split()))

        return ans


    def __str__(self):

        mul = '%s, '

        ans = 'Non-Terminals:\n\t'

        nonterminals = mul * (len(self.nonTerminals)-1) + '%s\n'

        ans += nonterminals % tuple(self.nonTerminals)

        ans += 'Terminals:\n\t'

        terminals = mul * (len(self.terminals)-1) + '%s\n'

        ans += terminals % tuple(self.terminals)

        ans += 'Productions:\n\t'

        ans += str(self.Productions)

        return ans

    def __getitem__(self, name):
        try:
            return self.symbDict[name]
        except KeyError:
            return None

    @property
    def to_json(self):

        productions = []

        for p in self.Productions:
            head = p.Left.Name

            body = []

            for s in p.Right:
                body.append(s.Name)

            productions.append({'Head':head, 'Body':body})

        d={'NonTerminals':[symb.Name for symb in self.nonTerminals], 'Terminals': [symb.Name for symb in self.terminals],\
         'Productions':productions}

         # [{'Head':p.Left.Name, "Body": [s.Name for s in p.Right]} for p in self.Productions]
        return json.dumps(d)

    @staticmethod
    def from_json(data):
        data = json.loads(data)

        G = Grammar()
        dic = {'epsilon':G.Epsilon}

        for term in data['Terminals']:
            dic[term] = G.Terminal(term)

        for noTerm in data['NonTerminals']:
            dic[noTerm] = G.NonTerminal(noTerm)

        for p in data['Productions']:
            head = p['Head']
            dic[head] %= Sentence(*[dic[term] for term in p['Body']])

        return G

    def copy(self):
        G = Grammar()
        G.Productions = self.Productions.copy()
        G.nonTerminals = self.nonTerminals.copy()
        G.terminals = self.terminals.copy()
        G.pType = self.pType
        G.startSymbol = self.startSymbol
        G.Epsilon = self.Epsilon
        G.EOF = self.EOF
        G.symbDict = self.symbDict.copy()

        return G

    @property
    def IsAugmentedGrammar(self):
        augmented = 0
        for left, right in self.Productions:
            if self.startSymbol == left:
                augmented += 1
        if augmented <= 1:
            return True
        else:
            return False

    def AugmentedGrammar(self, force=False):
        if not self.IsAugmentedGrammar or force:

            G = self.copy()
            # S, self.startSymbol, SS = self.startSymbol, None, self.NonTerminal('S\'', True)
            S = G.startSymbol
            G.startSymbol = None
            SS = G.NonTerminal('S\'', True)
            if G.pType is AttributeProduction:
                SS %= S + G.Epsilon, lambda x : x
            else:
                SS %= S + G.Epsilon

            return G
        else:
            return self.copy()
    #endchange

class Item:

    def __init__(self, production, pos, lookaheads=[]):
        self.production = production
        self.pos = pos
        self.lookaheads = frozenset(look for look in lookaheads)

    def __str__(self):
        s = str(self.production.Left) + " -> "
        if len(self.production.Right) > 0:
            for i,c in enumerate(self.production.Right):
                if i == self.pos:
                    s += "."
                s += str(self.production.Right[i])
            if self.pos == len(self.production.Right):
                s += "."
        else:
            s += "."
        s += ", " + str(self.lookaheads)[10:-1]
        return s

    def __repr__(self):
        return str(self)


    def __eq__(self, other):
        return (
            (self.pos == other.pos) and
            (self.production == other.production) and
            (set(self.lookaheads) == set(other.lookaheads))
        )

    def __hash__(self):
        return hash((self.production,self.pos,self.lookaheads))

    @property
    def IsReduceItem(self):
        return len(self.production.Right) == self.pos

    @property
    def NextSymbol(self):
        if self.pos < len(self.production.Right):
            return self.production.Right[self.pos]
        else:
            return None

    def NextItem(self):
        if self.pos < len(self.production.Right):
            return Item(self.production,self.pos+1,self.lookaheads)
        else:
            return None

    def Preview(self, skip=1):
        unseen = self.production.Right[self.pos+skip:]
        return [ unseen + (lookahead,) for lookahead in self.lookaheads ]

    def Center(self):
        return Item(self.production, self.pos)
    