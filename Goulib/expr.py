#!/usr/bin/env python
# coding: utf8
"""
simple symbolic math expressions
"""

__author__ = "Philippe Guglielmetti, J.F. Sebastian, Geoff Reedy"
__copyright__ = "Copyright 2013, Philippe Guglielmetti"
__credits__ = [
    'http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string',
    'http://stackoverflow.com/questions/3867028/converting-a-python-numeric-expression-to-latex',
    ]
__license__ = "LGPL"

import six, logging, copy, collections, inspect, re

from . import plot #sets matplotlib backend
import matplotlib.pyplot as plt # after import .plot

from . import itertools2

# http://stackoverflow.com/questions/2371436/evaluating-a-mathematical-expression-in-a-string

import ast
import operator as op

# supported operators with precedence and text + LaTeX repr
# precedence as in https://docs.python.org/2/reference/expressions.html#operator-precedence
#
operators = {
    ast.Or: (op.or_,300,' or ',' \\vee '),
    ast.And: (op.and_,400,' and ',' \\wedge '),
    ast.Not: (op.not_,500,'not ','\\neg'),
    ast.Eq: (op.eq,600,'=',' = '),
    ast.Gt: (op.gt,600,' > ',' \\gtr '),
    ast.GtE:(op.ge,600,' >= ',' \\gec '),
    ast.Lt: (op.lt,600,' < ',' \\ltr '),
    ast.LtE: (op.le,600,' <= ',' \\leq '),
    ast.BitXor: (op.xor,800,' xor ',' xor '),
    ast.LShift: (op.lshift, 1000,' << ',' \\ll '),
    ast.RShift: (op.rshift, 1000,' >> ',' \\gg '),
    ast.Add: (op.add, 1100,'+','+'),
    ast.Sub: (op.sub, 1100,'-','-'),
    ast.Mult: (op.mul, 1200,'*',' \\cdot '),
    ast.Div: (op.truediv, 1200,'/','/'),
    ast.Mod: (op.mod, 1200,'%','\\bmod'),
    ast.Invert: (op.not_,1300,'~','\\sim'),
    ast.UAdd: (op.pos,1300,'+','+'),
    ast.USub: (op.neg,1300,'-','-'),
    ast.Pow: (op.pow,1400,'**','^'),

    # precedence of other types below
    ast.Name:(None,9999),
    ast.Num:(None,9999),
    ast.Call:(None,9999),
}

import math
functions=math.__dict__ #allowed functions

def eval(node,context={}):
    """safe eval of ast node : only functions and operators listed above can be used
    """
    try:
        if isinstance(node, ast.Num): # <number>
            return node.n
        elif isinstance(node, ast.Name):
            return context.get(node.id,node.id) #return value or var
        elif isinstance(node, ast.Attribute):
            return getattr(context[node.value.id],node.attr)
        elif isinstance(node, ast.Call):
            params=[eval(arg,context) for arg in node.args]
            return functions[node.func.id](*params)
        elif isinstance(node, ast.BinOp): # <left> <operator> <right>
            return operators[type(node.op)][0](eval(node.left,context), eval(node.right,context))
        elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
            return operators[type(node.op)][0](eval(node.operand,context))
        elif isinstance(node, ast.Compare):
            left=eval(node.left,context)
            for op,right in zip(node.ops,node.comparators):
                #TODO: find what to do when multiple items in list
                return operators[type(op)][0](left, eval(right,context))
        else:
            return eval(node.body,context)
    except KeyError:
        raise NameError('%s function not allowed'%node.func.id)
    """
    except Exception as e:
        logging.error(ast.dump(node,False,False))
    """

def get_function_source(f):
    """returns cleaned code of a function or lambda
    currently only supports:
    - lambda x:formula_of_(x)
    - def anything(x): return formula_of_(x)
    """
    f=inspect.getsource(f).rstrip('\n') #TODO: merge lines more subtly
    g=re.search(r'lambda(.*):(.*)(\)|#)',f)
    if g:
        res=g.group(2).strip() #remove leading+trailing spaces
        bra,ket=res.count('('),res.count(')')
        if bra==ket:
            return res
        else: #closing parenthesis ?
            return res[:-(ket-bra)]
    else:
        g=re.search(r'def \w*\((.*)\):\s*return (.*)',f)
        if g is None:
            logging.error('not a valid function code %s'%f)
        res=g.group(2)
    return res


class Expr(plot.Plot):
    """
    Math expressions that can be evaluated like standard functions
    combined using standard operators
    and plotted in IPython/Jupyter notebooks
    """
    def __init__(self,f):
        """
        :param f: function or operator, Expr to copy construct, or formula string
        """

        if isinstance(f,Expr): #copy constructor
            self.body=f.body
            return
        elif isinstance(f,ast.AST):
            self.body=f
            return
        elif inspect.isfunction(f):
            f=get_function_source(f)
        elif isinstance(f, collections.Callable): # builtin function
            f='%s(x)'%f.__name__
        elif f in ('True','False'):
            f=bool(f)
        if type(f) is bool: 
            self.body=ast.Num(f)
            return

        self.body=compile(str(f),'Expr','eval',ast.PyCF_ONLY_AST).body

    def __call__(self,x=None,**kwargs):
        """evaluate the Expr at x OR compose self(x())"""
        if isinstance(x,Expr): #composition
            return self.applx(x)
        try: #is x iterable ?
            return [self(x) for x in x]
        except:
            if x is not None:
                kwargs['x']=x
            kwargs['self']=self #allows to call methods such as in Stats
            return eval(self.body,kwargs)

    def __repr__(self):
        return ast.dump(self.body,False,False)

    def __str__(self):
        return TextVisitor().visit(self.body)

    def _latex(self):
        """:return: string LaTex formula"""
        return LatexVisitor().visit(self.body)

    def _repr_latex_(self):
        return r'$%s$'%self._latex()

    def latex(self):
        from IPython.display import Math
        return Math(self._latex())

    def _plot(self, ax, x=None, y=None, **kwargs):
        if x is None:
            x=itertools2.arange(-1,1,.1)
        x=list(x)
        if y is None:
            y=self(x)
        y=list(y)

        offset=kwargs.pop('offset',0) #slightly shift the points to make superimposed curves more visible
        x=[_+offset for _ in x] # listify at the same time
        y=[_+offset for _ in y] # listify at the same time
        ax.plot(x,y, **kwargs)
        return ax

    def apply(self,f,right=None):
        """function composition self o f = f(self(x))"""

        if right is None:
            if isinstance(f, ast.unaryop):
                node=ast.UnaryOp(f,self.body)
            else:
                #if not isinstance(f,Expr): f=Expr(f) #not useful as applx does the reverse
                return f.applx(self)
        else:
            if not isinstance(right,Expr):
                right=Expr(right)
            node = ast.BinOp(self.body,f,right.body)
        return Expr(node)

    def applx(self,f,var='x'):
        """function composition f o self = self(f(x))"""
        if isinstance(f,Expr):
            f=f.body

        class Subst(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id==var:
                    return f
                else:
                    return node

        node=copy.deepcopy(self.body)
        return Expr(Subst().visit(node))

    @property
    def isconstant(self):
        try:
            self._y=eval(self.body)
            return True
        except Exception as e:
            return False

    def __eq__(self,other):
        if self.isconstant:
            try:
                if other.isconstant:
                    return self._y==other._y
            except:
                return self._y==other
        raise NotImplementedError #TODO: implement for general expressions...

    def __lt__(self,other):
        if self.isconstant:
            try:
                if other.isconstant:
                    return self._y<other._y
            except:
                return self._y<other
        raise NotImplementedError #TODO: implement for general expressions...

    def __add__(self,right):
        return self.apply(ast.Add(),right)

    def __sub__(self,right):
        return self.apply(ast.Sub(),right)

    def __neg__(self):
        return self.apply(ast.USub())

    def __mul__(self,right):
        return self.apply(ast.Mult(),right)

    def __rmul__(self,right):
        return Expr(right)*self

    def __truediv__(self,right):
        return self.apply(ast.Div(),right)

    __div__=__truediv__

    def __invert__(self):
        return self.apply(ast.Invert())

    def __and__(self,right):
        return self.apply(ast.And(),right)

    def __or__(self,right):
        return self.apply(ast.Or(),right)

    def __xor__(self,right):
        return self.apply(ast.BitXor(),right)

    def __lshift__(self,dx):
        return self.applx(ast.BinOp(ast.Name('x',None),ast.Add(),ast.Num(dx)))

    def __rshift__(self,dx):
        return self.applx(ast.BinOp(ast.Name('x',None),ast.Sub(),ast.Num(dx)))


#http://stackoverflow.com/questions/3867028/converting-a-python-numeric-expression-to-latex

class TextVisitor(ast.NodeVisitor):

    def prec(self, n):
        try:
            return operators[type(n)][1]
        except KeyError:
            return operators[type(n.op)][1]

    def prec_UnaryOp(self, n):
        return self.prec(n.op)

    def prec_BinOp(self, n):
        return self.prec(n.op)

    def visit_Call(self, n):
        func = self.visit(n.func)
        args = ', '.join(map(self.visit, n.args))
        return '%s(%s)' % (func, args)

    def visit_Name(self, n):
        return n.id

    def visit_UnaryOp(self, n):
        if self.prec(n.op) > self.prec(n.operand):
            return r'%s(%s)' % (operators[type(n.op)][2], self.visit(n.operand))
        else:
            return r'%s%s' % (operators[type(n.op)][2], self.visit(n.operand))

    def _Bin(self, left,op,right):
        # commute x*2 as 2*X for clarity
        if isinstance(op, ast.Mult):
            if isinstance(right, ast.Num) and not isinstance(left, ast.Num):
                return self._Bin(right,op,left)

        l,r = self.visit(left),self.visit(right)

        #handle precedence (parenthesis) if needed
        if self.prec(op) > self.prec(left):
            l = '(%s)' % l
        if self.prec(op) > self.prec(right):
            r = '(%s)' % r

        return l+operators[type(op)][2]+r

    def visit_BinOp(self, n):
        return self._Bin(n.left,n.op,n.right)

    def visit_Compare(self,n):
        #TODO: what to do with multiple ops/comparators ?
        return self._Bin(n.left,n.ops[0],n.comparators[0])

    def visit_Num(self, n):
        return str(n.n)

    def generic_visit(self, n):
        try:
            l=map(self.visit, n)
            return ''.join(l)
        except:
            pass

        if isinstance(n, ast.AST):
            l=map(self.visit, [getattr(n, f) for f in n._fields])
            return ''.join(l)
        else:
            return str(n)


class LatexVisitor(TextVisitor):


    def visit_Call(self, n):
        func = self.visit(n.func)
        args = ', '.join(map(self.visit, n.args))
        return r'\%s\left(%s\right)' % (func, args)

    def visit_UnaryOp(self, n):
        if self.prec(n.op) > self.prec(n.operand):
            return r'%s\left(%s\right)' % (operators[type(op)][3], self.visit(n.operand))
        else:
            return r'%s %s' % (operators[type(op)][3], self.visit(n.operand))

    def _Bin(self, left,op,right):
        # commute x*2 as 2*X for clarity
        if isinstance(op, ast.Mult):
            if isinstance(right, ast.Num) and not isinstance(left, ast.Num):
                return self._Bin(right,op,left)

        l,r = self.visit(left),self.visit(right)

        #handle divisions and power first as precedence doesn't matter
        if isinstance(op, ast.Div):
            return r'\frac{%s}{%s}' % (l, r)
        if isinstance(op, ast.FloorDiv):
            return r'\left\lfloor\frac{%s}{%s}\right\rfloor' % (l,r)
        if isinstance(op, ast.Pow):
            return r'%s^{%s}' % (l,r)

        #handle precedence (parenthesis) if needed
        if self.prec(op) > self.prec(left):
            l = r'\left(%s\right)' % l
        if self.prec(op) > self.prec(right):
            r = r'\left(%s\right)' % r

        if isinstance(op, ast.Mult):
            if isinstance(left, ast.Num) and not isinstance(right, ast.Num):
                return l+r

        return l+operators[type(op)][3]+r






