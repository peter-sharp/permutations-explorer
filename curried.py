import functools

def curried(arity):
    def curry(fn):
        args = []

        def with_args(*newArgs):
            nonlocal arity
            nonlocal args
            if len(args) + len(newArgs) == arity:
                return fn(*args, *newArgs)
            elif len(args) > arity:
                raise Exception(f"{fn.__name__} expects {arity} args {len(args)} given: {str(tuple(args))}")
            else:
                args = [*args, *newArgs]
                return functools.partial(fn, *args)
        return with_args
    return curry
