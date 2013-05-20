import nodes
import unittest

class NodesClass1(nodes.GraphObject):

    @nodes.graphMethod(nodes.Settable)
    def A(self):
        return 'A' + self.B() + self.C()

    @nodes.graphMethod(nodes.Settable)
    def B(self):
        return 'B'

    @nodes.graphMethod(nodes.Settable)
    def C(self):
        return 'C' + self.D()

    @nodes.graphMethod(nodes.Settable)
    def D(self):
        return 'D'

class NodesTest(unittest.TestCase):

    def setUp(self):
        self.o = NodesClass1()

    def assertInitialGraphValues(self):
        o = self.o
        self.assertEquals(o.A(), 'ABCD')
        self.assertEquals(o.B(), 'B')
        self.assertEquals(o.C(), 'CD')
        self.assertEquals(o.D(), 'D')

    def test_simple_context(self):
        o = self.o
        with nodes.GraphContext():
            o.A.overlayValue('abcd')
            self.assertEquals(o.A(),  'abcd')
            self.assertEquals(o.B(), 'B')
            self.assertEquals(o.C(), 'CD')
            self.assertEquals(o.D(), 'D')
        self.assertInitialGraphValues()
        with nodes.GraphContext():
            o.B.overlayValue('b')
            self.assertEquals(o.B(), 'b')
            self.assertEquals(o.A(), 'AbCD')
            self.assertEquals(o.C(), 'CD')
            self.assertEquals(o.D(), 'D')
            o.C.overlayValue('c')
            self.assertEquals(o.C(), 'c')
            self.assertEquals(o.A(), 'Abc')
            o.A.overlayValue('a')
            self.assertEquals(o.A(), 'a')
            o.A.clearOverlay()
            self.assertEquals(o.A(), 'Abc')
            o.B.clearOverlay()
            self.assertEquals(o.A(), 'ABc')
            o.C.clearOverlay()
            self.assertEquals(o.A(), 'ABCD')
            o.C.overlayValue('c')
            o.D.overlayValue('d')
            self.assertEquals(o.A(), 'ABc')
            o.C.clearOverlay()
            self.assertEquals(o.A(), 'ABCd')

    def test_context_plus_overlays(self):
        o = self.o
        self.assertInitialGraphValues()
        with nodes.GraphContext() as c:
            o.A.overlayValue('abcd')
            self.assertEquals(o.A(), 'abcd')
        self.assertInitialGraphValues()
        with c:
            self.assertEquals(o.A(), 'abcd')
            o.A.clearOverlay()
            self.assertEquals(o.A(), 'ABCD')
            o.B.overlayValue('b')
            self.assertEquals(o.A(), 'AbCD')
            self.assertEquals(o.B(), 'b')
            o.A.overlayValue('aBcd')
            self.assertEquals(o.A(), 'aBcd')
            o.B.overlayValue('3')
            self.assertEquals(o.A(), 'aBcd')
            self.assertEquals(o.B(), '3')
            o.A.clearOverlay()
            self.assertEquals(o.A(), 'A3CD')
        self.assertInitialGraphValues()
        with c:
            self.assertEquals(o.B(), 'B')
            self.assertEquals(o.A(), 'abcd')
        self.assertInitialGraphValues()

    def test_remove_inherited_overlay(self):
        o = self.o
        self.assertInitialGraphValues()
        with nodes.GraphContext() as c1:
            o.B.overlayValue('b')
            self.assertEquals(o.B(), 'b')
            self.assertEquals(o.A(), 'AbCD')
            o.B.clearOverlay()
            self.assertEquals(o.B(), 'B')
            self.assertEquals(o.A(), 'ABCD')
        self.assertInitialGraphValues()
        with c1:
            self.assertInitialGraphValues()
        with nodes.GraphContext() as c2:
            o.B.overlayValue('b')
            o.B.clearOverlay()
            o.B.overlayValue('3')
            self.assertEquals(o.B(), '3')
        self.assertInitialGraphValues()
        with c2:
            self.assertEquals(o.A(), 'A3CD')
            self.assertEquals(o.B(), '3')
            o.B.clearOverlay()
            self.assertEquals(o.A(), 'ABCD')
            self.assertEquals(o.B(), 'B')
        self.assertInitialGraphValues()
        with c1:
            self.assertInitialGraphValues()
            with c2:
                self.assertEquals(o.A(), 'A3CD')
                self.assertEquals(o.B(), '3')
            self.assertInitialGraphValues()
        self.assertInitialGraphValues()

if __name__ == '__main__':
    unittest.main()

