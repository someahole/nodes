nodes
=====

An easy-to-use graph-oriented object model for Python.

Example
-------

    import nodes

    class Example(nodes.GraphObject):

        @nodes.graphmethod
        def X(self):
            return 'X:%s:%s' % (self.Y(), self.Z())
      
        @nodes.graphmethod(nodes.Settable)
        def Y(self):
            return 'Y'
             
        @nodes.graphmethod(nodes.Settable)
        def Z(self):
            return 'Z'
     
        def main():                     
            example = Example()
         
            # Run a computation for the first time.  This triggers
            # execution of the function body, which also results in
            # Y and Z being called.
            #
            print example.X()    # Prints 'X:Y:Z'
            
            # At this point X, Y, and Z have all been computed and 
            # memoized. So the following calls would return the 
            # memoized value.
            #
            print example.X()    # Prints 'X:Y:Z'
            print example.Y()    # Prints 'Y' 
            print example.Z()    # Prints 'Z' 
            
            # Now we change Y:
            #
            example.Y = 'y'      # Syntactic sugar for example.Y.setValue('y')   
            
            # X depends on Y, so X is invalidated.  Y is set directly, 
            # so it is valid, and Z is still valid from the earlier computation.
            #
            print example.X()    # Prints 'X:y:Z'
            example.Y.clearValue()
            
            print example.X()    # Prints 'X:Y:Z'
            with nodes.Context():
                example.Z.overlayValue('z')
                print example.X()    # Prints 'X:Y:z'
            
            print example.X()    # Prints 'X:Y:Z'    
            with nodes.Context() as c:
                example.Y.overlayValue('y')
                example.Z.overlayValue('z')
            
            print example.X()      # Prints 'X:Y:Z'
            with c:
                print example.X()  # Prints 'X:y:z'
                with nodes.Context():
                    example.Z.overlayValue('')
                    print example.X()    # Prints 'X:y:'
                print example.X()  # Prints 'X:y:z'
            print example.X()      # Prints 'X:Y:Z'
