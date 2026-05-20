from session_lattice.views import tool_sessions

# Ordered list of view modules. Each module exposes `materialize(con)` and
# `NAME`. The refresh tick calls them sequentially after the puller writes
# its base tables. Order matters when one view depends on another.
ALL = [tool_sessions]
