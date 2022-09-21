import linecache

from tippo import Any, Callable


def generate_unique_filename(cls, func_name):
    """
    Create a "filename" suitable for a function being generated.
    """
    return "<generated {} {}.{}>".format(
        func_name, cls.__module__, getattr(cls, "__fullname__", getattr(cls, "__qualname__", cls.__name__))
    )


def make_method(name, script, filename, globs):
    # type: (str, str, str, dict[str, Any]) -> Callable
    """
    Create the method with the script given and return the method object.
    """
    locs = {}  # type: dict[str, Any]

    # In order of debuggers like PDB being able to step through the code,
    # we add a fake linecache entry.
    count = 1
    base_filename = filename
    while True:
        linecache_tuple = (
            len(script),
            None,
            script.splitlines(True),
            filename,
        )  # type: tuple[int, float | None, list[str], str]
        old_val = linecache.cache.setdefault(filename, linecache_tuple)
        if old_val == linecache_tuple:
            break
        else:
            filename = "{}-{}>".format(base_filename[:-1], count)
            count += 1

    compile_and_eval(script, globs, locs, filename)

    return locs[name]


def compile_and_eval(script, globs, locs=None, filename=""):
    """
    "Exec" the script with the given global (globs) and local (locs) variables.
    """
    bytecode = compile(script, filename, "exec")
    eval(bytecode, globs, locs)
