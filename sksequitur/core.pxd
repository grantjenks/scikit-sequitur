cdef class Symbol:
    cdef dict bigrams
    cdef Symbol next_symbol, prev_symbol
    cdef object value
    cpdef append(self, object value)
    cpdef join(self, Symbol right)
    cdef _remove_bigram(self)
    cpdef check(self)
    cdef _process_match(self, Symbol match)
    cdef _substitute(self, Rule rule)
    cdef _delete(self)
    cdef _expand(self)
    cdef _bigram(self)

cdef class Rule(Symbol):
    pass
