"""nodes: An easy-to-use graph-based object model for Python.

"""
import collections
import copy
import types

Settable     = 0x1
Serializable = 0x2
Saved        = Settable | Serializable

class Graph(object):
    """Plumbing that drives and manages updates to and
    computations of nodes in a directed acyclic graph.

    """
    def __init__(self):
        self.nodes = {}             # All active nodes in the graph, by node key.
        self.activeNode = None
        self.activeGraphContext = None

    def lookupNode(self, graphObject, graphMethod, args, create=True):
        """Returns the Node underlying the given object and its method
        as called with the specified arguments.

        """
        key = (graphObject, graphMethod) + args
        if key not in self.nodes and create:
            self.nodes[key] = Node(graphObject, graphMethod, args=args)
        return self.nodes.get(key)

    def isComputing(self):
        """Returns True if the graph is currently computing a value,
        False otherwise.

        The impact of computation is that no other graph modifications
        (sets and overlays, that is) can be updated.

        """
        # The test is simple at the moment: if a node is active,
        # we're computing.
        #
        return self.activeNode

    def getValue(self, node):
        """Returns the value of the node, recalculating if necessary,
        honoring any active graph context.

        """
        # TODO: Consider rewriting as a visitor or context.
        #
        outputNode = graph.activeNode
        try:
            if outputNode:
                outputNode.addInput(node)
                node.addOutput(outputNode)
            graph.activeNode = node
            return node.getValue()
        finally:
            graph.activeNode = outputNode

    def setValue(self, node, value):
        """Sets for value for a node, assuming the node
        permits it to be set.

        """
        if self.activeNode:
            raise RuntimeError("You cannot set a node during graph evaluation.")
        node.setValue(value)

    def clearSet(self, node):
        """Clears the current node if it has been set.

        Raises an exception if the node has not been
        set.

        Note that clearing a value is not the same as
        forcing its clearing its memoized, calculated
        value, if one is present.

        """
        if self.activeNode:
            raise RuntimeError("You cannot clear a set value during graph evaluation.")
        node.clearSet()

    def overlayValue(self, node, value):
        if self.activeNode:
            raise RuntimeError("You cannot overlay a node during graph evaluation.")
        if not self.activeGraphContext:
            raise RuntimeError("You cannot overlay a node outside a graph context.")
        self.activeGraphContext.overlayValue(node, value)

    def clearOverlay(self, node):
        if self.activeNode:
            raise RuntimeError("You cannot clear a overlay during graph evaluation.")
        if not self.activeGraphContext:
            raise RuntimeError("You cannot clear a overlay outside a graph context.")
        self.activeGraphContext.clearOverlay(node)


class GraphVisitor(object):
    """Visits a hierarchy of graph nodes in depth first order.

    Assumes the node has been evaluated at least once so
    that its inputs have been updated.  Even this is imperfect
    and is one downside of the dynamic apporach.

    """
    # TODO: I only support node visitation at the moment, so
    #       I'm avoiding overhead of the double-dispatch here,
    #       indeed, it would probably get a getattr() call not a 
    #       method call on the graph object.
    #
    def visit(self, node):
        yetToVisit = [node]
        while yetToVisit:
            yetToVisit.extend(self.visitNode(yetToVisit.pop(0)))

    def visitNode(self, node):
        """Visits a node and returns a list of additional nodes
        to visit.

        """
        raise NotImplementedError()

class GraphContext(object):
    """A graph context is collection of temporary node changes
    that can be applied and unapplied without modifying the
    top-level node settings.

    Contexts can be saved to variables and passed around,
    and are applied using Python with statement.

    """
    def __init__(self, parentGraphContext=None):
        self._parentGraphContext = parentGraphContext
        self._overlays      = {}   # Node overlays by node.
        self._state       = {}   # Node values by node.
        self._applied     = set()

    def addOverlay(self, node, value):
        """Add a new overlay to the graph context, but does not apply it to the node.

        """
        self._overlays[node] = value

    def removeOverlay(self, node):
        """Removes a overlay from the graph context, but does not unapply it from
        the node.

        """
        del self._overlays[node]

    def overlayValue(self, node, value):
        """Adds a overlay to the graph context and immediately applies it to
        the node.

        """
        if node in self._overlays:
            self.removeOverlay(node)
        self.addOverlay(node, value)
        self.applyOverlay(node)

    def applyOverlay(self, node):
        """Applies a overlay to a node, stashing away any existing
        overlays (from another graph context) that were inherited so we can
        reapply them later.

        """
        if node.isOverlayed() and node not in self._applied:
            self._state[node] = node.getOverlay()
        node.overlayValue(self.getOverlay(node))
        self._applied.add(node)

    def clearOverlay(self, node):
        """Removes the overlay from the node, restoring old state,
        and, if this overlay was in the current graph context, also
        removes it from the overlay data.

        """
        # If the node was overlayed in this graph context, we need to restore any
        # existing overlays that may have been applied outside of this
        # graph context. 
        #
        if self.hasOverlay(node) and self.isOverlayed(node):
            # If the node had a value that we stashed away, restore it.
            # Otherwise, clear it.
            if node in self._state:
                # TODO: I reoverlay here - which kind of seems wrong in that the
                #       original overlay was never really "removed," but at present
                #       will work for our cases.  This also has the side-effect 
                #       of invalidating the parent node, which again is something
                #       we want because the node was invalidated when we applied
                #       our overlays.  Nevertheless, it'd be nice to merely preserve
                #       the original state and avoid the recalculation of the 
                #       parent nodes if they really don't need to be recalculated.
                #
                #       Also we don't clear our existing overlay here, relying on
                #       fact that overlaying the node will essentially do that for us.
                #
                node.overlayValue(self._state[node])
                del self._state[node]
            else:
                node.clearOverlay()
            self._applied.remove(node)

    def isOverlayed(self, node):
        """Return True if a overlay in this graph context (or any of its parents)
        is active on the node.

        """
        return node in self._applied

    def hasOverlay(self, node, includeParent=True):
        """Returns True if a overlay exists for the node in this
        graph context.

        """
        if node in self._overlays:
            return True
        if includeParent and self._parentGraphContext:
            return self._parentGraphContext.hasOverlay(node)
        return False

    def allOverlays(self, includeParent=True):
        """Returns a list of all overlays presnet in the graph context.

        If includeParent is True (the default) also includes
        parent overlays that haven't been overlayed specifically
        in this graph context.

        """
        if not includeParent or not self._parentGraphContext:
            return self._overlays.copy()
        overlays = self._parentGraphContext.allOverlays()
        overlays.update(self._overlays)
        return overlays

    def getOverlay(self, node, includeParent=True):
        """Returns the overlay for the specified
        node as it exists within this graph context.

        """
        return self.allOverlays(includeParent=includeParent)[node]

    def __enter__(self):
        """Enter the graph context, activating any overlays it contains.

        Note that overlays always override already-applied overlays, so
        if overlays have been applied in a higher graph context, stash those
        away to be restored when we exit the context.

        """
        self.activeParentGraphContext = graph.activeGraphContext
        graph.activeGraphContext = self
        for node in self.allOverlays():
            self.applyOverlay(node)
        return self

    def __exit__(self, *args):
        """Exit the graph context and remove any applied overlays.

        """
        for node in self.allOverlays():
            self.clearOverlay(node)
        graph.activeGraphContext = self.activeParentGraphContext

class GraphMethod(object):
    """An unbound graph-enabled method.

    Holds state and settings that all instances of an object
    containing this method

    """

    def __init__(self, method, name, flags=0, delegateTo=None):
        """Creates a , which lifts a regular method
        into a version that supports graph-based dependency
        tracking and other graph features.

        When an instance of a class inheriting from GraphObject
        is created, any  methods defined on it are
        bounded to the instance as GraphInstanceMethods.

        By default all GraphInstanceMethods are read-only
        (i.e., cannot be set or overlayed, and always derive values
        via their underlying method).

        Use flags to modify this default behavior.

        Flags available:
            * Settable      The value can be directly set by a user.
            * Serializable  The value (whether set or computed) will be
                            extracted as part of object state.
            * Saved         Equivalent to setting both Settable and Serializable.

        delegateTo is optional and if provided must be set to
        can be set to a callable.  In that case, when the value of the
        GraphInstanceMethod is set by a user (via a setValue operation),
        a call to the callable is made instead, passing in the value
        the user specified.

        The delegate must returns a list of NodeChange objects,
        each of which is a mapping between another GraphInstanceMethod
        and the value it will be set to.

        """
        self.method = method
        self.name = name
        self.flags = flags
        self.delegateTo = delegateTo

    def isSettable(self):
        """Returns True if a bound instance of the
        can be set by a user, or False otherwise.

        """
        return self.flags & Settable

    def isSerializable(self):
        """Returns True if the value of a bound instance of the
        should be included as part of the object's state
        during serialization routines.  Otherwise returns False.

        This would also typically mean that the graph method
        is settable as well, though this is not strictly
        required.

        """
        return self.flags & Serializable

    def isSaved(self):
        """Equivalent to setting the Settable and Serializable
        flags on the graph method.

        The reasoning is that we have no desire to save purely
        computed values, so we only save settable ones that
        are also serializable.

        Returns True if both flaas are set, or False otherwise.
        """
        return self.flags & Saved == Saved

    def delegatesChanges(self):
        """Returns True if changes to this method are handled
        by a delegate that itself is responsible for
        returning a list of the actual desired changes.

        """
        return self.delegateTo is not None

    def __call__(self, graphObject, *args):
        """A short-cut to calling the underlying method with the supplied
        arguments.

        """
        return self.method(graphObject, *args)

# TODO: Consider introducing the notion of a value store, 
#       either at the graph context level or elsewhere, generalizing 
#       the case of how we store and manage node value.
#
class Node(object):
    """A node on the graph.

    A node is uniquely identified by

        (graphObject, graphMethod, args)

    and a GraphInstanceMethod maps to one or more nodes differentiated
    by the arguments used to call it.

    """
    def __init__(self, graphObject, graphMethod, args=()):
        """Creates a new node on the graph.

        Fundamentally a node represents a value that is either
        calculated or directly specified by a user.

        """
        self.graphObject = graphObject
        self.graphMethod = graphMethod
        self.args = args

        # A node has a list of the nodes that depend upon it as well 
        # as the nodes that it depends upon. I call these outputs 
        # and inputs, respectively.  
        #
        # These relationships are maintained by the graph engine,
        # which has the logic for how to construct a graph.
        # A node is mainly responsible for (re)calculating its
        # value (or returning it if already set) and for invalidating
        # anything that relies upon it.
        #
        # TODO: I may want to model these more generally as edges,
        #       allowing us to set attributes on them, but for now
        #       the two lists will suffice.
        #       
        self._outputs = set()
        self._inputs = set()

        # TODO: This is a bit of a hack.  If I set a value and then
        #       overlay it, for example, there's no immediate reason
        #       I shouldn't be able to merely restore the old value.
        #       For now this state is mained here, which works 
        #       on the assumption that setting a node is a root
        #       operation but overlaying it is temporary and graph context-
        #       specific.
        #
        self._isOverlayed    = False
        self._isSet        = False
        self._isCalced     = False

        # TODO:  I'm maintaining values for overlays, sets, and calcs 
        #        each in a separate namespace, which is necessary 
        #        if we wish to reavoid calculating when, for example,
        #        overlays are set, but maintaining them within the node 
        #        itself is questionable.  I need to rethink this.
        #
        self._overlayedValue = None
        self._setValue     = None
        self._calcedValue  = None

    def addInput(self, inputNode):
        """Informs the node of an input dependency, which indicates
        the node requires the input node's value to complete
        its own computation.

        Input nodes are only used when a node has not been set
        directly (via a setValue or overlayValue operation).

        """
        self._inputs.add(inputNode)


    def addOutput(self, outputNode):
        """Informs the node of a new output, that is, a node
        that depends on the current node for its own value.

        When the current node is invalidated it invalidates
        its outputs as well.

        """
        self._outputs.add(outputNode)

    def removeInput(self, inputNode):
        """Removes the specified node from the list of required
        inputs, or does nothing if the node is not a known
        input.

        """
        if node in self._inputs:
            self._inputs.remove(inputNode)

    def removeOutput(self, outputNode):
        """Removes the output from the list of node outputs, or
        does nothing if the node is not a known output.

        """
        if node in self._outputs:
            self._outputs.remove(outputNode)

    @property
    def outputs(self):
        return self._outputs

    @property
    def inputs(self):
        return self._inputs

    def getValue(self):
        """Return the node's current value, recalculating if necessary.

        If the current value is valid, there is no need to recalculate it.

        """
        # TODO: See comment above regarding the split of these 
        #       tests and the variables used to store values based on 
        #       how a node was fixed/calced.  Short story: this will
        #       be rewritten.
        #
        if self.isOverlayed():
            return self._overlayedValue
        if self.isSet():
            return self._setValue
        if not self.isCalced():
            self.calcValue()
        return self._calcedValue

    def calcValue(self):
        """(Re)calculates the value of this node my calling
        its underlying method on graph, and updating the
        stored value and status of the calculation
        accordingly.

        Note that this method will force a recalculation
        even if the current calculation is valid.  The result
        of the recalculation should in that case be exactly
        the same as the result already calculated.  If it
        is not then either the method is not pure or there
        is an issue with the graph.

        """
        self._calcedValue = self.graphMethod(self.graphObject, *self.args)
        self._isCalced = True

    def _invalidateCalc(self):
        """Removes any calculated value, forcing a recalculation
        the next time the node has no set or overlayed value.

        """
        self._invalidateOutputCalcs()
        self._isCalced = False
        self._calcedValue = False

    def _invalidateOutputCalcs(self):
        """Invalidates any outputs that were dependent on this
        node as part of a calculation.

        """
        for output in self._outputs:
            output._invalidateCalc()

    def setValue(self, value):
        """Sets a specific value on the node.

        Setting a value invalidates known outputs that are not set
        themselves.

        """
        if not self.graphMethod.isSettable():
            raise RuntimeError("You cannot set a read-only node.")
        self._invalidateOutputCalcs()
        self._setValue = value
        self._isSet = True

    def clearSet(self):
        """Clears a previously set value on the node, if
        any.

        """
        if not self.graphMethod.isSettable():
            raise RuntimeError("You cannot clear a read-only node.")
        if not self.isSet():
            return
        self._invalidateOutputCalcs()
        self._isSet = False
        self._setValue = None

    def overlayValue(self, value):
        """Overlays the value of the node.  At this level a overlay
        is merely a value stored in a different namespace that
        nonetheless invalidates any output nodes.

        """
        # TODO: Perhaps optimize for _overlayedValue == value case.
        self._invalidateOutputCalcs()
        self._overlayedValue = value
        self._isOverlayed = True

    def clearOverlay(self):
        """Clears the current overlay, if any, invalidating
        outputs if a overlay was actually cleared.

        """
        if not self.isOverlayed():
            return
        self._invalidateOutputCalcs()
        self._isOverlayed = False
        self._overlayedValue = None

    def getOverlay(self):
        """Returns the value of the current overlay, if any, or
        raises an exception otherwise.

        """
        if not self.isOverlayed():
            raise Exception("This node is not overlayed.")
        return self._overlayedValue

    def isValid(self):
        """Returns True if the node does not need recomputation.

        """
        return self._isOverlayed or self._isSet or self._isCalced

    def isOverlayed(self):
        """Returns True if this node is overlayed, False otherwise.

        Overlays are independent of sets and calcs.

        """
        return self._isOverlayed

    def isSet(self):
        """Return True if this node was set to an explicit value.

        In that case it will no longer be recomputed or invalidated
        if its dependencies change.

        """
        return self._isSet

    def isCalced(self):
        """Return True if the value was calculated.

        """
        return self._isCalced

    def node(self):
        return self

    def __repr__(self):
        return '<Node graphObject=%r;graphMethod=%s;args=%s>' % (
                self.graphObject,
                self.graphMethod,
                self.args
                )

    def __str__(self):
        return '<Node %s.%s(%s) isSet=%s;isOverlayed=%s;isCalced=%s>' % (
                self.graphObject.__class__.__name__,
                self.graphMethod.name,
                str(self.args),
                self.isSet(),
                self.isOverlayed(),
                self.isCalced()
                )


class NodeChange(object):
    """Encapsulates a pending change to a node, as returned
    by a delegation function.

    """
    def __init__(self, graphInstanceMethod, value, *args):
        self.graphObject = graphInstanceMethod.graphObject
        self.graphMethod = graphInstanceMethod.graphMethod
        self.value = value
        self.args = args

    @property
    def node(self):
        return graph.lookupNode(self.graphObject, self.graphMethod, self.args, create=True)


class GraphInstanceMethod(object):
    """A  bound to an instance of its class.

    A GraphInstanceMethod provides the interface between the user object
    and the graph.

    """
    def __init__(self, graphObject, graphMethod):
        self.graphObject = graphObject
        self.graphMethod = graphMethod

    def node(self, *args):
        return graph.lookupNode(self.graphObject, self.graphMethod, args, create=True)

    def __call__(self, *args):
        return self.getValue(*args)

    def getValue(self, *args):
        """Returns the current value of underlying node based on the current
        graph state.

        """
        return graph.getValue(self.node(*args))

    def setValue(self, value, *args):
        # TODO: Is this the right place for delegation, or should
        #       we do that within the node implementation?  I
        #       don't like it in Node, because a node doesn't know
        #       about the global graph state.  We could put it in
        #       a higher level (perhaps in graph.setValue()) perhaps.
        #       There is a lot of coupling between all of these
        #       things but the code is simple enough it should be
        #       easy to refactor as needs demand.
        #
        if self.graphMethod.delegatesChanges():
            nodeChanges = self.graphMethod.delegateTo(self.graphObject, value, *args)
            for nodeChange in nodeChanges:
                graph.setValue(nodeChange.node, nodeChange.value)
            return
        graph.setValue(self.node(*args), value)

    def clearSet(self, *args):
        graph.clearSet(self.node(*args))

    def overlayValue(self, value, *args):
        graph.overlayValue(self.node(*args), value)

    def clearOverlay(self, *args):
        graph.clearOverlay(self.node(*args))

class GraphType(type):
    """Metaclass responsible for creating on-graph objects.

    """
    def __init__(cls, name, bases, attrs):
        for k,v in attrs.items():
            if isinstance(v, GraphMethod) and v.name != k:
                v_ = copy.copy(v)
                v_.name = k
                v_.flags = v.flags
                setattr(cls, k, v_)

        type.__init__(cls, name, bases, attrs)

        if name != 'GraphObject' and '__init__' in cls.__dict__:
            raise RuntimeError("GraphObject {} is not permitted to override __init__".format(name))

        graphMethods = []
        for k in dir(cls):
            v = getattr(cls, k)
            if isinstance(v, GraphMethod):
                graphMethods.append(v)
        cls._graphMethods = graphMethods
        cls._savedGraphMethods = [graphMethod for graphMethod in graphMethods if graphMethod.isSaved()]

class DB(object):
    """A database of GraphObjects.

    """
    # TODO: A placeholder until a real database interface has been introduced.

    LIMBO = '/limbo'    # Limbo objects don't have a true path and cannot be written out.

    def __getitem__(self, path):
        return self.read(path)

    def new(self, typeName, path=None, **kwargs):
        """Create a new object of the specified type
        with the given path (or in limbo, if no path
        is specified), optionally initialized with
        the given kwargs.

        """
        raise NotImplementedError()

    def readOrNew(self, typeName, path=None, **kwargs):
        if self.exists(path):
            return self.read(path)
        return self.new(typeName, path, **kwargs)

    def exists(self, path):
        raise NotImplementedError()

    def read(self, path):
        raise NotImplementedError()

    def readObj(self, path):
        raise NotImplementedError()

    def readMany(self, paths):
        return [self.readObj(path) for path in paths]

    def write(self, obj):
        raise NotImplementedError()

currentDb = DB()

class GraphObject(object):
    """A graph-enabled object.

    """
    __metaclass__ = GraphType

    _path  = None
    _isnew = True

    db = currentDb

    def path(self):
        return self._path

    def isnew(self):
        return self._isnew

    def __setattr__(self, name, value):
        v = getattr(self, name)
        if isinstance(v, GraphInstanceMethod):
            v.setValue(value)
            return
        object.__setattr__(self, name, value)

    def __init__(self, **kwargs):
        for k in dir(self):
            v = getattr(self, k)
            if isinstance(v, GraphMethod):
                object.__setattr__(self, k, GraphInstanceMethod(self, getattr(self,k)))
        for k,v in kwargs.items():
            attr = getattr(self, k)
            if not isinstance(attr, GraphInstanceMethod):
                raise RuntimeError("Not a GraphInstanceMethod: %s" % k)
            self.__setattr__(attr.graphMethod.name, v)

    def toDict(self):
        """Returns a dictionary of name/value pairs for all saved methods.

        """
        return dict([(k.name, getattr(self, k.name)()) for k in self._savedGraphMethods])

def graphMethod(thingy=0, delegateTo=None):
    """Declare a GraphObject method as on-graph.

    """
    if type(thingy) == types.FunctionType:
        return GraphMethod(thingy, thingy.__name__)
    flags = thingy
    def wrap(f):
        return GraphMethod(f, f.__name__, flags, delegateTo=delegateTo)
    return wrap

graph = Graph()

# TODO: Add a node garbage collector (perhaps weakref).
# TODO: Add multithreading support.
# TODO: Add database storage support.
# TODO: Add subscriptions.
# TODO: Productionize for large-scale use (perhaps with CPython).
