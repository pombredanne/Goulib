#!/usr/bin/env python
# coding: utf8
"""
additions to :mod:`itertools` standard library
"""
__author__ = "Philippe Guglielmetti"
__copyright__ = "Copyright 2012, Philippe Guglielmetti"
__credits__ = ["functional toolset from http://pyeuler.wikidot.com/toolset",
               "algos from https://github.com/tokland/pyeuler/blob/master/pyeuler/toolset.py",
               "tools from http://docs.python.org/dev/py3k/library/itertools.html",
               ]
__license__ = "LGPL"

import six #Python2+3 compatibility utilities
import random, operator, collections, heapq, itertools

#reciepes from Python manual

def take(n, iterable):
    """
    :result: first n items from iterable
    """
    return itertools.islice(iterable, n)

def index(n, iterable):
    """
    :result: nth item
    """
    for i,x in enumerate(iterable):
        if i==n: return x
    raise IndexError

def first(iterable):
    """
    :result: first element in the iterable
    """
    for x in iterable:
        return x # works in all cases by definition of iterable
    raise IndexError


def last(iterable):
    """
    :result: last element in the iterable
    """
    found=False
    for x in iterable:
        found=True
    if found:
        return x
    raise IndexError

def takeevery(n, iterable, first=0):
    """Take an element from iterator every n elements"""
    return itertools.islice(iterable, first, None, n)

every=takeevery

def drop(n, iterable):
    """Drop n elements from iterable and return the rest"""
    return itertools.islice(iterable, n, None)

def ilen(it):
    """
    :result: int length exhausing an iterator
    """
    return sum(1 for _ in it)

def irange(start_or_end, optional_end=None):
    """
    :result: iterable that counts from start to end (both included).
    """
    if optional_end is None:
        start, end = 0, start_or_end
    else:
        start, end = start_or_end, optional_end
    return take(max(end - start + 1, 0), itertools.count(start))

def isiterable(obj):
    """
    :result: bool True if obj is iterable (but not a string)
    """
    return hasattr(obj, '__iter__')

def arange(start,stop=None,step=1):
    """ range for floats or other types (`numpy.arange` without numpy)
    
    :param start: optional number. Start of interval. The interval includes this value. The default start value is 0.
    :param stop: number. End of interval. The interval does not include this value, except in some cases where step is not an integer and floating point round-off affects the length of out.
    :param step: optional number. Spacing between values. For any output out, this is the distance between two adjacent values, out[i+1] - out[i]. The default step size is 1. 
    :result: iterator
    """
    if stop is None:
        stop=start
        start=0
    r = start
    step=abs(step)
    if stop<start :
        while r > stop:
            yield r
            r -= step
    else:
        while r < stop:
            yield r
            r += step

def linspace(start,end,n=100):
    """ iterator over n values linearly interpolated between (and including) start and end
    `numpy.linspace` without numpy
    
    :param start: number, or iterable vector
    :param end: number, or iterable vector
    :param n: int number of interpolated values
    :result: iterator
    """
    # try: #suppose start and end are tuples or lists of the same size
    if isiterable(start):
        res=(linspace(s,e,n) for s,e in zip(start,end))
        return zip(*res)
    # like http://www.mathworks.com/help/matlab/ref/linspace.html
    # http://docs.scipy.org/doc/numpy/reference/generated/numpy.linspace.html has more options
    if start==end: #generate n times the same value for consistency
        return itertools.repeat(start,n)
    else: #make sure we generate n values including start and end
        step=float(end-start)/(n-1)
        return arange(start,end+step/2,step)

def flatten(l, donotrecursein=six.string_types):
    """iterator to flatten (depth-first) structure
    
    :param l: iterable structure
    :param donotrecursein: tuple of iterable types in which algo doesn't recurse
                           string type by default
    """
    #http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python
    for el in l:
        if not isinstance(el, collections.Iterable):
            yield el
        elif isinstance(el, donotrecursein):
            yield el
        else:
            for sub in flatten(el,donotrecursein):
                yield sub

def itemgetter(iterable,i):
    for item in iterable:
        yield item[i]

def compact(iterable,f=bool):
    """
    :returns: iterator skipping None values from iterable
    """
    return filter(f, iterable)

def compress(iterable):
    """
    generates (item,count) paris by counting the number of consecutive items in iterable)
    """
    prev,count=None,0
    for item in iterable:
        if item==prev and count:
            count+=1
        else:
            if count: #to skip initial junk
                yield prev,count
            prev=item
            count=1
    if count:
        yield prev,count

def tee(iterable, n=2, copy=None):
    """tee or copy depending on type and goal
    
    :param iterable: any iterable
    :param n: int number of tees/copies to return
    :param copy: optional copy function, for exemple copy.copy or copy.deepcopy
    :result: tee of iterable if it's an iterator or generator, or (deep)copies for other types

    this function is useful to avoid side effects at a lower memory cost
    depending on the case
    """
    if isinstance(iterable,(list,tuple,set,dict)):
        if copy is None: # same object replicated n times
            res=[iterable]*n
        else:
            res=[copy(iterable) for _ in range(n)]
        return tuple(res)
    return itertools.tee(iterable,n) # make independent iterators

def groups(iterable, n, step=None):
    """Make groups of 'n' elements from the iterable advancing
    'step' elements on each iteration"""
    itlist = tee(iterable, n=n, copy=None)
    onestepit = six.moves.zip(*(itertools.starmap(drop, enumerate(itlist))))
    return every(step or n, onestepit)

def pairwise(iterable,op=None,loop=False):
    """
    iterates through consecutive pairs
    
    :param iterable: input iterable s1,s2,s3, .... sn
    :param op: optional operator to apply to each pair
    :param loop: boolean True if last pair should be (sn,s1) to close the loop
    :result: pairs iterator (s1,s2), (s2,s3) ... (si,si+1), ... (sn-1,sn) + optional pair to close the loop
    """

    i=itertools.chain(iterable,[first(iterable)]) if loop else iterable
    for x in groups(i,2,1):
        if op:
            yield op(x[1],x[0]) #reversed ! (for sub or div)
        else:
            yield x[0],x[1]
            
def reshape(data,dims):
    """
    :result: data as a n-dim matrix
    """
    data=list(flatten(data))
    for d in dims[::-1]: #reversed
        if d:
            data=[data[i:i+d] for i in range(0,len(data),d)]
        else:
            data=[data]
    return data[0]


def compose(f, g):
    """Compose two functions -> compose(f, g)(x) -> f(g(x))"""
    def _wrapper(*args, **kwargs):
        return f(g(*args, **kwargs))
    return _wrapper

def iterate(func, arg):
    """After Haskell's iterate: apply function repeatedly."""
    # not functional
    while True:
        yield arg
        arg = func(arg)

def accumulate(iterable, func=operator.add, skip_first=False):
    """Return running totals. extends `python.itertools.accumulate`
    
    # accumulate([1,2,3,4,5]) --> 1 3 6 10 15
    # accumulate([1,2,3,4,5], operator.mul) --> 1 2 6 24 120
    """
    first=True
    for x in iterable:
        if first:
            total=x
            first=False
            if skip_first: continue
        else:
            total = func(total, x)
        yield total

def tails(seq):
    """Get tails of a sequence
    
    tails([1,2,3]) -> [1,2,3], [2,3], [3], [].
    """
    for idx in range(len(seq)+1):
        yield seq[idx:]

def ireduce(func, iterable, init=None):
    """Like `python.reduce` but using iterators (a.k.a scanl)"""
    # not functional
    if init is None:
        iterable = iter(iterable)
        curr = six.next(iterable)
    else:
        curr = init
        yield init
    for x in iterable:
        curr = func(curr, x)
        yield curr

def unique(iterable, key=None):
    """generate unique elements, preserving order. Remember all elements ever seen.
    
    # unique('AAAABBBCCDAABBB') --> A B C D
    # unique('ABBCcAD', str.lower) --> A B C D
    """
    seen = set()
    for element in iterable:
        k = key(element) if key else element
        if k not in seen:
            seen.add(k)
            yield element

def count_unique(iterable, key=None):
    """Count unique elements
    
    # count_unique('AAAABBBCCDAABBB') --> 4
    # count_unique('ABBCcAD', str.lower) --> 4
    """
    seen = set()
    for element in iterable:
        seen.add(key(element) if key else element)
    return len(seen)

def identity(x):
    """Do nothing and return the variable untouched"""
    return x

def occurrences(it, exchange=False):
    """Return dictionary with occurrences from iterable"""
    return six.moves.reduce(lambda occur, x: dict(occur, **{x: occur.get(x, 0) + 1}), it, {})

def cartesian_product(*iterables, **kwargs):
    """http://stackoverflow.com/questions/12093364/cartesian-product-of-large-iterators-itertools
    """
    if len(iterables) == 0:
        yield ()
    else:
        iterables = iterables * kwargs.get('repeat', 1)
        it = iterables[0]
        for item in it() if isinstance(it, collections.Callable) else iter(it):
            for items in cartesian_product(*iterables[1:]):
                yield (item, ) + items

# my functions added

def any(seq, pred=bool):
    """
    :result: bool True if pred(x) is True for at least one element in the iterable
    """
    return (True in map(pred, seq))

def all(seq, pred=bool):
    """
    :result: bool True if pred(x) is True for all elements in the iterable
    """
    return (False not in map(pred, seq))

def no(seq, pred=bool):
    """
    :result: bool True if pred(x) is False for every element in the iterable
    """
    return (True not in map(pred, seq))

def takenth(n, iterable, default=None):
    """
    :result: nth item of iterable
    """
    # https://docs.python.org/2/library/itertools.html#recipes
    return six.next(itertools.islice(iterable, n, n+1),default)

nth=takenth

def icross(*sequences):
    """Cartesian product of sequences (recursive version)"""
    # http://stackoverflow.com/questions/15099647/cross-product-of-sets-using-recursion
    if sequences:
        for x in sequences[0]:
            for y in icross(*sequences[1:]):
                yield (x,)+y
    else: yield ()

def quantify(iterable, pred=bool):
    """
    :result: int count how many times the predicate is true
    """
    return sum(map(pred, iterable),0)

def interleave(l1,l2):
    """
    :param l1: iterable
    :param l2: iterable of same length, or 1 less than l1
    :result: iterable interleaving elements from l1 and l2, starting by l1[0]
    """
    # http://stackoverflow.com/questions/7946798/interleaving-two-lists-in-python-2-2
    res=l1+l2
    res[::2]=l1
    res[1::2]=l2
    return res

def shuffle(ary):
    """
    :param: array to shuffle by Fisher-Yates algorithm
    :result: shuffled array (IN PLACE!)
    :see: http://www.drgoulu.com/2013/01/19/comment-bien-brasser-les-cartes/
    """
    for i in range(len(ary)-1,0,-1):
        j=random.randint(0,i)
        ary[i],ary[j]=ary[j],ary[i]
    return ary

def rand_seq(size):
    """
    :result: range(size) shuffled
    """
    return shuffle(list(range(size)))

def all_pairs(size):
    """generates all i,j pairs for i,j from 0-size"""
    for i in rand_seq(size):
        for j in rand_seq(size):
            yield (i,j)

def index_min(values, key=identity):
    """
    :result: min_index, min_value
    """
    return min(enumerate(values), key=lambda v:key(v[1]))

def index_max(values, key=identity):
    """
    :result: min_index, min_value
    """
    return max(enumerate(values), key=lambda v:key(v[1]))

def best(iterable, key=None, n=1, reverse=False):
    """ generate items corresponding to the n best values of key sort order"""
    v=sorted(iterable,key=key,reverse=reverse)
    if key is None : key=identity
    i,k=0,None
    for x in v:
        k2=key(x)
        if k2==k:
            yield x
        else:
            k=k2
            i+=1
            if i>n: break #end
            yield x

def sort_indexes(iterable, key=identity, reverse=False):
    """
    :return: iterator over indexes of iterable that correspond to the sorted iterable
    """
    # http://stackoverflow.com/questions/6422700/how-to-get-indices-of-a-sorted-array-in-python
    return [i[0] for i in sorted(enumerate(iterable), key=lambda x:key(x[1]))]

# WARNING : filter2 has been renamed from "split" at v.1.7.0 for coherency
def filter2(iterable,condition):
    """ like `python.filter` but returns 2 lists :
    - list of elements in iterable that satisfy condition
    - list of those that don't
    """
    yes,no=[],[]
    for x in iterable:
        if condition(x):
            yes.append(x)
        else:
            no.append(x)
    return yes,no

def ifind(iterable,f,reverse=False):
    """iterates through items in iterable where f(item) == True."""
    if not reverse:
        for i,item in enumerate(iterable):
            if f(item):
                yield (i,item)
    else:
        l=len(iterable)-1
        for i,item in enumerate(reversed(iterable)):
            if f(item):
                yield (l-i,item)

def iremove(iterable,f):
    """
    removes items from an iterable based on condition
    :param iterable: iterable . will be modified in place
    :param f: function of the form lambda line:bool returning True if item should be removed
    :yield: removed items backwards
    """
    for i,_ in ifind(iterable,f,reverse=True):
        yield iterable.pop(i)

def removef(iterable,f):
    """
    removes items from an iterable based on condition
    :param iterable: iterable . will be modified in place
    :param f: function of the form lambda line:bool returning True if item should be removed
    :result: list of removed items.
    """
    res=list(iremove(iterable,f))
    res.reverse()
    return res

def find(iterable,f):
    """Return first item in iterable where f(item) == True."""
    return six.next(ifind(iterable,f))

def isplit(iterable,sep,include_sep=False):
    """ split iterable by separators or condition
    :param sep: value or function(item) returning True for items that separate
    :param include_sep: bool. If True the separators items are included in output, at beginning of each sub-iterator
    :result: iterates through slices before, between, and after separators
    """
    indexes=(i for i,_ in ifind(iterable,sep))
    indexes=itertools.chain([0 if include_sep else -1],indexes,[None]) # will be the last j
    for i,j in pairwise(indexes):
        yield itertools.islice(iterable,i if include_sep else i+1,j)

def split(iterable,sep,include_sep=False):
    """ like https://docs.python.org/2/library/stdtypes.html#str.split, but for iterable
    :param sep: value or function(item) returning True for items that separate
    :param include_sep: bool. If True the separators items are included in output, at beginning of each sub-iterator
    :result: list of iterable slices before, between, and after separators
    """
    return [list(x) for x in isplit(iterable,sep,include_sep)]

def dictsplit(dic,keys):
    """ extract keys from dic
    :param dic: dict source
    :param keys: iterable of dict keys
    :result: dict,dict : the first contains entries present in source, the second the remaining entries
    """
    yes,no={},dic.copy()
    for k in keys:
        if k in no:
            yes[k]=no.pop(k)
    return yes,no

def next_permutation(seq, pred=lambda x,y:-1 if x<y else 0):
    """Like C++ std::next_permutation() but implemented as generator.
    see http://blog.bjrn.se/2008/04/lexicographic-permutations-using.html
    :param seq: iterable
    :param pred: a function (a,b) that returns a negative number if a<b, like cmp(a,b) in Python 2.7
    """

    def reverse(seq, start, end):
        # seq = seq[:start] + reversed(seq[start:end]) + \
        #       seq[end:]
        end -= 1
        if end <= start:
            return
        while True:
            seq[start], seq[end] = seq[end], seq[start]
            if start == end or start+1 == end:
                return
            start += 1
            end -= 1

    if not seq:
        raise StopIteration

    try:
        seq[0]
    except TypeError:
        raise TypeError("seq must allow random access.")

    first = 0
    last = len(seq)
    seq = seq[:]

    # Yield input sequence as the STL version is often
    # used inside do {} while.
    yield seq

    if last == 1:
        raise StopIteration

    while True:
        next = last - 1

        while True:
            # Step 1.
            next1 = next
            next -= 1

            if pred(seq[next], seq[next1]) < 0:
                # Step 2.
                mid = last - 1
                while not (pred(seq[next], seq[mid]) < 0):
                    mid -= 1
                seq[next], seq[mid] = seq[mid], seq[next]

                # Step 3.
                reverse(seq, next1, last)

                # Change to yield references to get rid of
                # (at worst) |seq|! copy operations.
                yield seq[:]
                break
            if next == first:
                raise StopIteration
    raise StopIteration

class iter2(object):
    """Takes in an object that is iterable.
    http://code.activestate.com/recipes/578092-flattening-an-arbitrarily-deep-list-or-any-iterato/
    Allows for the following method calls (that should be built into iterators anyway...)
    calls:
    - append - appends another iterable onto the iterator.
    - insert - only accepts inserting at the 0 place, inserts an iterable before other iterables.
    - adding.  an iter2 object can be added to another object that is
    iterable.  i.e. iter2 + iter (not iter + iter2).
    It's best to make all objects iter2 objects to avoid syntax errors.  :D
    """
    def __init__(self, iterable):
        self._iter = iter(iterable)

    def append(self, iterable):
        self._iter = itertools.chain(self._iter, iter(iterable))

    def insert(self, place, iterable):
        if place != 0:
            raise ValueError('Can only insert at index of 0')
        self._iter = itertools.chain(iter(iterable), self._iter)

    def __add__(self, iterable):
        return itertools.chain(self._iter, iter(iterable))

    def __next__(self):
        return six.next(self._iter)

    next=__next__ #Python2-3 compatibility

    def __iter__(self):
        return self

def subdict(d,keys):
    """extract "sub-dictionary"
    :param d: dict
    :param keys: container of keys to extract:
    :result: dict:
    :see: http://stackoverflow.com/questions/5352546/best-way-to-extract-subset-of-key-value-pairs-from-python-dictionary-object/5352649#5352649
    """
    return dict([(i, d[i]) for i in keys if i in d])

def sorted_iterable(iterable, key=None, buffer=100):
    """sorts an almost sorted (infinite) iterable
    :param iterable: iterable
    :param key: function used as sort key
    :param buffer: int size of buffer. elements to swap should not be further than that
    """
    from Goulib.container import SortedCollection
    b=SortedCollection(key=key)
    for x in iterable:
        if len(b)>=buffer:
            yield b.pop(0)
        b.insert(x)
    for x in b: yield x # this never happens if iterable is infinite

# operations on sorted iterators

def unique_sorted(iterable):
    """generates items in sorted iterable without repetition"""
    prev=None
    for x in iterable:
        if x!=prev:
            yield x
        prev=x

def diff(iterable1,iterable2):
    """generate items in sorted iterable1 that are not in sorted iterable2"""
    b=six.next(iterable2)
    for a in iterable1:
        while b<a:
            b=six.next(iterable2)
        if a==b: continue
        yield a

merge=heapq.merge

#http://stackoverflow.com/questions/969709/joining-a-set-of-ordered-integer-yielding-python-iterators
def intersect(*its):
    for key, values in itertools.groupby(heapq.merge(*its)):
        if len(list(values)) == len(its):
            yield key


