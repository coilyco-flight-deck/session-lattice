from session_lattice.views import tool_sessions

# Ordered list of view modules. Each exposes `materialize(con)` and `NAME`.
# refresh._tick calls them sequentially after the puller; order matters across deps.
ALL = [tool_sessions]
