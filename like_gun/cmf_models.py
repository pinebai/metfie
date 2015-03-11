'''cmf_models.py defines classes for representing model choices that keep
track of provenance.
'''
class Provenance:
    '''A tree structure designed to track the origins of a Component
    instance.
    '''
    def __init__(
            self,
            frame,        # inspect.stack() reference to code that called
            text=None,    # Explanatory text
            branches=None,# A list or tuple of source Components
            max_depth=5
            ):
        self.file = frame[1]             # Name of file
        self.line = frame[2]             # Line number of file
        self.text = frame[4][0].strip()  # text of the specified line
        if text != None:
            self.text +='\n'+text
        if branches == None:
            self.leaf = True
            self.depth = 0
            self.branches = ()
        else:
            self.depth = max(x.depth for x in branches) + 1
            self.branches = tuple(branches)
            assert self.depth <= max_depth,'max depth exceeded\n{0}'.format(
                str(self))
    def _indent(self, root_depth):
        '''return a string description of self indented by (root_depth -
        self.depth).  The method calls itself to indent each branch of
        the provenance tree by depth.
        '''
        space = (root_depth - self.depth)*4*' '
        lines = self.text.splitlines()
        rv = '\n'+space+'depth={0:d}, {1} line {2:d}:{3}\n'.format(
            self.depth, self.file, self.line, lines[0])
        for line in lines[1:]:
            rv += space+line+'\n'
        for branch in self.branches:
            rv += branch._indent(root_depth)
        return rv
    def __str__(self):
        return self._indent(self.depth)
    def html(
            self,       # Provenance instance
            name,       # Component name
            root_depth,
            stub,       # Markup object to which this should "add"
            ):
        '''Add to h html view of self.
        '''
        from markup import oneliner
        key = '{0}_{1:d}'.format(name, root_depth-self.depth)
        stub.add(oneliner.dt(key,id=key))
        stub.add(oneliner.dd(oneliner.a('filename',href='dummy')))
        for branch in self.branches:
            branch.html(name, root_depth, stub)
        return

class Component:
    '''Parent class intended for subclasses.  A Component object represents a
    decision about an aspect of a model for simulation.  Examples
    include material properties like an entire EOS or just a heat
    capacity.
    
    '''
    def __init__(
        self,           # Component instance
        value,          # Subclasses may restrict this
        comment='',     # String of explanation
        provenance=None
        ):

        assert not type(self) == Component,'only use subclasses of Component'
        self.value = value
        if provenance == None: # Probably a leaf
            from inspect import stack
            # stack()[2] is context that called for Component sub_class
            self.provenance = Provenance(stack()[2], comment)
        else:
            self.provenance = provenance
    def __join__(self, value, comment, branches):
        '''return a new instance that is the result of an operation on
         the objects described by x_prov and y_prov
        '''
        from inspect import stack
        # stack()[2] is context that called for combination
        provenance = Provenance(stack()[2], comment, branches)
        
        # The following gets a new instance of same class as self even
        # if self is an instance of a subclass
        return self.__class__(value, comment, provenance)
    def __str__(self):
        rv= '''{0}, value = {1}, provenance:
{2}'''.format(self.__class__, self.value, self.provenance)
        return rv
    def html(
            self, # Component instance
            name, # Component name
            ):
        '''Return tuple containing:
             
             1. html description of self suitable for page.li()
             
             2. html description of provenance sutible for page.add
                inside of page.dl(), page.dl.close() pair
        '''
        from markup import oneliner
        return '{0}: value={1}, {2}'.format(
            name,
            self.value,
            oneliner.a('provenance',href='"#{0}_0"'.format(name))
            )
class Float(Component):
    '''
    '''
    def __init__(self, *args, **kwargs):
        import numbers
        assert isinstance(args[0], numbers.Number)
        Component.__init__(self, *args, **kwargs)
    def __add__(self, x):
        import numbers
        branches = [self.provenance]
        if isinstance(x, Component):
            x_value = x.value
            branches.append(x.provenance)
            comment = 'Added two Components'
        else:
            x_value = x
            comment = 'Added Component to number without provenance'
        assert isinstance(x_value, numbers.Number)
        rv = self.__join__(self.value+x_value, comment, branches)
        return rv

def test():
    comment = '''This is a long
multi line explanation
of the value 2.7
which is b in test'''
    a = Float(1)
    b = Float(27,comment)
    c = a+b
    d = c + 3
    print('''
a=%s
-----------------------------------------------------------------
a+b=%s
-----------------------------------------------------------------
c+3=%s
    '''%(str(a), str(c), str(d)))
    for i in range(6):
        a += i/2
    return 0
def make_html(component_dict, sorted_names=None, title='Simulation'):
    '''
    '''
    import markup
    if sorted_names == None:
        sorted_names = sorted(component_dict.keys())
    page = markup.page()
    page.h1('The components of {0}'.format(title))
    page.ul()
    for name, component in component_dict.items():
        page.li(component_dict[name].html(name))
    page.ul.close()
    page.br( )
    
    page.h1('Provenance of components')
    page.dl()
    for name, component in component_dict.items():
        # FixMe: modify page here if possible
        component.provenance.html(name, component.provenance.depth, page)
    page.dl.close()
    return page
def demo():
    import calc

    vt = calc.experiment()
    fit,e = calc.best_fit(vt)
    keys = sorted(fit.components)
    component_dict = dict((key,getattr(fit, key)) for key in keys)
    page = make_html(component_dict, keys, 'Simulated Gun')
    file_ = open('gun.html','wt')
    file_.write(page.__str__())
    return 0
    print(page)
    print("provenance of the components of simulated gun:")
    for key in keys:
        print('component {0}: {1}'.format(key, component_dict[key]))
    raise RuntimeError
    return 0
if __name__ == "__main__":
    demo()
    #test()

#---------------
# Local Variables:
# mode: python
# End: