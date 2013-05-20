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

    def test_simple_context(self):
        o = self.o
        with nodes.GraphContext():
            o.A.overlayValue('abcd')
            self.assertEquals(o.A(),  'abcd')
            self.assertEquals(o.B(), 'B')
            self.assertEquals(o.C(), 'CD')
            self.assertEquals(o.D(), 'D')
        self.assertEquals(o.A(), 'ABCD')
        self.assertEquals(o.B(), 'B')
        self.assertEquals(o.C(), 'CD')
        self.assertEquals(o.D(), 'D')
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

if __name__ == '__main__':
    unittest.main()

