from __future__ import annotations

from typing import Dict, Iterable, List, Tuple

import networkx as nx
from pycparser import c_ast


NodeId = int


class CFGBuilder:
    """
    Build a control-flow graph (CFG) from a pycparser AST.

    The resulting graph is a `networkx.DiGraph` where:
    - nodes represent program points (statements, conditions, entry/exit),
    - edges represent possible control-flow transitions.
    """

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._next_id: int = 0

    # ------------------------------------------------------------------
    # Node helpers
    # ------------------------------------------------------------------
    def _new_node(self, node_type: str, coord: c_ast.Coord | None = None) -> NodeId:
        """
        Create a new CFG node with metadata.

        Parameters
        ----------
        node_type:
            High-level node category, e.g. "stmt", "if", "while", "for", etc.
        coord:
            Optional source coordinate object; line is extracted if present.
        """
        node_id: NodeId = self._next_id
        self._next_id += 1

        line = coord.line if coord is not None and getattr(coord, "line", None) else None
        self.graph.add_node(node_id, type=node_type, line=line)
        return node_id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build(self, ast: c_ast.FileAST) -> nx.DiGraph:
        """Build and return a CFG for the whole translation unit."""
        for ext in ast.ext:
            if isinstance(ext, c_ast.FuncDef):
                self._build_function(ext)
        return self.graph

    # ------------------------------------------------------------------
    # Function-level construction
    # ------------------------------------------------------------------
    def _build_function(self, func: c_ast.FuncDef) -> None:
        """Construct CFG subgraph for a single function definition."""
        func_name = func.decl.name if hasattr(func.decl, "name") else "<anon>"

        entry = self._new_node("func_entry", func.decl.coord)
        exit_ = self._new_node("func_exit", func.decl.coord)

        # Mark function name on entry/exit nodes for easier debugging.
        self.graph.nodes[entry]["func"] = func_name
        self.graph.nodes[exit_]["func"] = func_name

        # Connect function body statements.
        body_items = list(func.body.block_items or [])
        exits = self._build_stmt_list(body_items, [entry])

        # Any path that leaves the function without an explicit return
        # connects to the function exit node.
        for last in exits:
            if last is not None:
                self.graph.add_edge(last, exit_)

    # ------------------------------------------------------------------
    # Statement sequence helpers
    # ------------------------------------------------------------------
    def _build_stmt_list(
        self,
        stmts: Iterable[c_ast.Node],
        incoming: List[NodeId],
    ) -> List[NodeId]:
        """
        Connect a sequence of statements.

        `incoming` is the set of predecessor nodes that flow into the first
        statement. The returned list contains exit nodes that flow out of
        the final statement in the sequence.
        """
        prevs = list(incoming)
        for stmt in stmts:
            prevs = self._build_stmt(stmt, prevs)
        return prevs

    def _build_stmt(self, stmt: c_ast.Node, incoming: List[NodeId]) -> List[NodeId]:
        """
        Build CFG edges for a single statement.

        This function returns a list of exit nodes that represent the points
        where control can leave this statement and flow into the next one.
        """
        # Compound statements (blocks) are treated as sequences.
        if isinstance(stmt, c_ast.Compound):
            items = list(stmt.block_items or [])
            if not items:
                # Empty block; control flows through unchanged.
                return list(incoming)
            return self._build_stmt_list(items, incoming)

        # If statements introduce a branch in the control flow.
        if isinstance(stmt, c_ast.If):
            return self._build_if(stmt, incoming)

        # Loop constructs.
        if isinstance(stmt, c_ast.While):
            return self._build_while(stmt, incoming)

        if isinstance(stmt, c_ast.For):
            return self._build_for(stmt, incoming)

        if isinstance(stmt, c_ast.DoWhile):
            return self._build_dowhile(stmt, incoming)

        # Return statements terminate the current path within the function.
        if isinstance(stmt, c_ast.Return):
            node = self._new_node("return", stmt.coord)
            for prev in incoming:
                self.graph.add_edge(prev, node)
            # No successors: returning ends this path; caller is responsible
            # for connecting this to a function-exit node if desired.
            return []

        # Default: generic statement node.
        node = self._new_node("stmt", getattr(stmt, "coord", None))
        for prev in incoming:
            self.graph.add_edge(prev, node)
        return [node]

    # ------------------------------------------------------------------
    # Specific constructs
    # ------------------------------------------------------------------
    def _build_if(self, stmt: c_ast.If, incoming: List[NodeId]) -> List[NodeId]:
        """
        Build CFG for an if/else construct.

        The condition node branches into two possible subgraphs: the 'then'
        and 'else' bodies. The exits of both branches are returned so that
        they can be connected to subsequent statements.
        """
        cond_node = self._new_node("if", stmt.coord)
        for prev in incoming:
            self.graph.add_edge(prev, cond_node)

        # THEN branch
        then_exits: List[NodeId]
        if stmt.iftrue is not None:
            then_exits = self._build_stmt(stmt.iftrue, [cond_node])
        else:
            # Empty then-branch: falls through directly after the if.
            then_exits = [cond_node]

        # ELSE branch
        else_exits: List[NodeId]
        if stmt.iffalse is not None:
            else_exits = self._build_stmt(stmt.iffalse, [cond_node])
        else:
            # No else-branch: control may skip the 'then' body.
            else_exits = [cond_node]

        return then_exits + else_exits

    def _build_while(self, stmt: c_ast.While, incoming: List[NodeId]) -> List[NodeId]:
        """
        Build CFG for a while-loop.

        The condition node is evaluated before each iteration. From the
        condition, control can either enter the body or exit the loop.
        """
        cond_node = self._new_node("while", stmt.coord)
        for prev in incoming:
            self.graph.add_edge(prev, cond_node)

        # Body executes only if condition is true.
        if stmt.stmt is not None:
            body_exits = self._build_stmt(stmt.stmt, [cond_node])
        else:
            body_exits = [cond_node]

        # Back-edge: from end of body back to the loop condition.
        for node in body_exits:
            self.graph.add_edge(node, cond_node)

        # When the condition evaluates to false, control flows out of the loop.
        # The condition node itself represents this exit point.
        return [cond_node]

    def _build_for(self, stmt: c_ast.For, incoming: List[NodeId]) -> List[NodeId]:
        """
        Build CFG for a for-loop.

        The for-loop is approximated as:
            init; while (cond) { body; next; }
        """
        # Initialization executes once before the loop.
        if stmt.init is not None:
            init_exits = self._build_stmt(stmt.init, incoming)
        else:
            init_exits = list(incoming)

        cond_node = self._new_node("for", stmt.coord)
        for prev in init_exits:
            self.graph.add_edge(prev, cond_node)

        # Body part
        if stmt.stmt is not None:
            body_exits = self._build_stmt(stmt.stmt, [cond_node])
        else:
            body_exits = [cond_node]

        # Iteration expression (e.g., i++) executes after each body.
        if stmt.next is not None:
            iter_exits = self._build_stmt(stmt.next, body_exits)
        else:
            iter_exits = body_exits

        # Back-edge: from iteration step back to the condition.
        for node in iter_exits:
            self.graph.add_edge(node, cond_node)

        # Condition false: control exits the loop from the condition node.
        return [cond_node]

    def _build_dowhile(self, stmt: c_ast.DoWhile, incoming: List[NodeId]) -> List[NodeId]:
        """
        Build CFG for a do-while loop.

        The body executes at least once, then the condition determines whether
        control repeats the body or exits the loop.
        """
        # First iteration: enter body directly.
        if stmt.stmt is not None:
            body_exits = self._build_stmt(stmt.stmt, incoming)
        else:
            body_exits = list(incoming)

        cond_node = self._new_node("do_while", stmt.cond.coord if hasattr(stmt, "cond") else None)

        # From body to condition.
        for node in body_exits:
            self.graph.add_edge(node, cond_node)

        # If condition is true, control returns to body entry.
        # For simplicity, we treat the condition node as redirecting back to
        # the first body node(s) by adding back-edges.
        # Here we approximate by forming an edge back to itself to indicate a loop.
        self.graph.add_edge(cond_node, cond_node)

        # When condition is false, control exits from the condition node.
        return [cond_node]


def build_cfg(ast: c_ast.FileAST) -> nx.DiGraph:
    """
    High-level helper to build a CFG from a C AST.
    """
    builder = CFGBuilder()
    return builder.build(ast)

