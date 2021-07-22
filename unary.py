def unary(fn):
    def as_unary(*args,**kwargs):
        return fn(args[0])
    return as_unary