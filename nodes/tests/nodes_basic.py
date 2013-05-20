import nodes
import unittest

class NodesClass1(nodes.GraphObject):

    @nodes.graphMethod
    def A(self):
        return self.B() + self.C()

    @nodes.graphMethod(nodes.Settable)
    def B(self):
        return 'x'

    @nodes.graphMethod(nodes.Settable)
    def C(self):
        return 'y' + self.D()

    @nodes.graphMethod(nodes.Settable)
    def D(self):
        return 'z'

class NodesClass2(nodes.GraphObject):

    @nodes.graphMethod(nodes.Settable)
    def E(self):
        return self.F(self.G())

    @nodes.graphMethod(nodes.Settable)
    def F(self, v):
        return 'x' + (v or '-')

    @nodes.graphMethod(nodes.Settable)
    def G(self):
        return 'y'

class NodesClass3(nodes.GraphObject):

    def changeB(self, value):
        return [nodes.NodeChange(self.B, value)]

    @nodes.graphMethod(delegateTo=changeB)
    def A(self):
        return None

    @nodes.graphMethod(nodes.Settable)
    def B(self):
        return None

class NodesClass4(nodes.GraphObject):

    @nodes.graphMethod
    def SetX(self):
        self.X = False

    @nodes.graphMethod(nodes.Settable)
    def X(self):
        return True

class NodesTest1(unittest.TestCase):

    def test_simple(self):
        o = NodesClass1()

        self.assertFalse(o.A.node().isValid())
        self.assertFalse(o.A.node().isSet())
        self.assertFalse(o.B.node().isValid())
        self.assertFalse(o.B.node().isSet())
        self.assertFalse(o.C.node().isValid())
        self.assertFalse(o.C.node().isSet())
        self.assertFalse(o.D.node().isValid())
        self.assertFalse(o.D.node().isSet())
        self.assertEquals(o.A(), 'xyz')
        self.assertEquals(o.B(), 'x')
        self.assertEquals(o.C(), 'yz')
        self.assertEquals(o.D(), 'z')

        self.assertTrue(o.A.node().isValid())
        self.assertFalse(o.A.node().isSet())
        self.assertTrue(o.B.node().isValid())
        self.assertFalse(o.B.node().isSet())
        self.assertTrue(o.C.node().isValid())
        self.assertFalse(o.C.node().isSet())
        self.assertTrue(o.D.node().isValid())
        self.assertFalse(o.D.node().isSet())

        o.D = 'q'
        self.assertFalse(o.A.node().isValid())
        self.assertFalse(o.A.node().isSet())
        self.assertTrue(o.B.node().isValid())
        self.assertFalse(o.B.node().isSet())
        self.assertFalse(o.C.node().isValid())
        self.assertFalse(o.C.node().isSet())
        self.assertTrue(o.D.node().isValid())
        self.assertTrue(o.D.node().isSet())
        self.assertEquals(o.A(), 'xyq')
        self.assertEquals(o.B(), 'x')
        self.assertEquals(o.C(), 'yq')
        self.assertEquals(o.D(), 'q')

        o.D.clearSet()
        self.assertEquals(o.A(), 'xyz')
        self.assertEquals(o.B(), 'x')
        self.assertEquals(o.C(), 'yz')
        self.assertEquals(o.D(), 'z')

        o.C = 'z'
        self.assertEquals(o.A(), 'xz')
        self.assertEquals(o.B(), 'x')
        self.assertEquals(o.C(), 'z')
        self.assertEquals(o.D(), 'z')

        o.D = 'y'
        self.assertEquals(o.A(), 'xz')
        self.assertEquals(o.B(), 'x')
        self.assertEquals(o.C(), 'z')
        self.assertEquals(o.D(), 'y')

        o.D.clearSet()
        self.assertEquals(o.A(), 'xz')
        self.assertEquals(o.B(), 'x')
        self.assertEquals(o.C(), 'z')
        self.assertEquals(o.D(), 'z')

        o.C.clearSet()
        self.assertEquals(o.A(), 'xyz')
        self.assertEquals(o.C(), 'yz')
        self.assertEquals(o.D(), 'z')

        def trySettingA(o):
            o.A = ''

        self.assertRaises(Exception, callableObj=trySettingA, args=(o,))


    def test_args(self):
        o = NodesClass2()

        self.assertEquals(o.E(), 'xy')
        self.assertEquals(o.F(None), 'x-')
        self.assertEquals(o.G(), 'y')

        o.F.setValue('z', 'y')
        self.assertEquals(o.E(), 'z')

        o.G = 'q'
        self.assertEquals(o.E(), 'xq')

        o.G.clearSet()
        self.assertEquals(o.E(), 'z')

        o.F.clearSet('y')
        self.assertEquals(o.E(), 'xy')

        o.E = 'xyz'
        self.assertEquals(o.E(), 'xyz')
        o.E.clearSet()
        self.assertEquals(o.E(), 'xy')

    def test_nodeChange(self):
        o = NodesClass3()

        o.A = 'x'
        self.assertEquals(o.A(), None)
        self.assertEquals(o.B(), 'x')

    def test_cantSetOnAComputingGraph(self):
        o = NodesClass4()
        self.assertEquals(o.X(), True)
        self.assertRaises(RuntimeError, callableObj=o.SetX)
        self.assertEquals(o.X(), True)

if __name__ == '__main__':
    unittest.main()



