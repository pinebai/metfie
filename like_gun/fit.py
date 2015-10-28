"""fit.py: Coordinates optimization for fitting a model eos to experiments.


"""
import numpy as np
class go:
    ''' Generic object.  For storing magic numbers.
    '''
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
magic = go(
    D_frac=2.0e-2,     # Fractional finte difference for esimating dv/df
    fit_dim=50,        # Number of x points for EOS fit
    max_iter=5,        # Bound for iterations maximizing likelihood
    converge=1.0e-5,   # Fractional tolerance for cost
           )
class Opt:
    def __init__(
            self,        # Opt instance
            eos,         # eos.Spline_eos instance
            experiment,  # Dict of experimental simulation objects
            data,        # Dict of experimental data
            ):
        '''
        '''
        self.eos = eos
        self.original_eos = eos
        self.experiment = experiment
        self.data = data
        assert set(experiment.keys()) == set(data.keys())
        return
    def step(self, constrain=True, debug=False):
        ''' Do a constrained optimization step
        '''
        old_c = self.eos.get_c().copy()

        ########### Set up quadratic program ####################
        G,h = self.eos.Gh(old_c)         # Constraint
        P,q = self.eos.Pq_prior(old_c)   # Objective
        for k in self.data.keys():
            P_, q_ = self.eos.Pq_like(
                *self.experiment[k].compare(self.data[k], old_c))
            P += P_
            q += q_
        from cvxopt import matrix, solvers
        solvers.options['show_progress']=False#True
        solvers.options['maxiters']=1000 # 100 default
        solvers.options['reltol']=1e-8   # 1e-6 default
        solvers.options['abstol']=1e-9   # 1e-7 default
        solvers.options['feastol']=1e-12 # 1e-7 default
        if constrain:
            sol=solvers.qp(matrix(P), matrix(q), matrix(G), matrix(h) )
        else:
            sol=solvers.qp(matrix(P), matrix(q))
        if sol['status'] != 'optimal':
            for key,value in sol.items():
                print(key, value)
            raise RuntimeError
        d_hat = np.array(sol['x']).reshape(-1)
        ########### d_hat is solution of quadratic program ######
        
        if self.eos.precondition:
            d_hat = np.dot(self.eos.U_inv, d_hat)
        n_steps = 10
        costs = np.empty(n_steps)
        xs = np.linspace(0,1, n_steps)
        for i,x in enumerate(xs):
            costs[i] = self.cost(old_c + d_hat*x, debug=debug)
        i = np.argmin(costs)
        self.eos = self.eos.new_c(old_c + d_hat*xs[i])
        return costs[i], costs
    def fit(
            self,                # Opt instance
            max_it=magic.max_iter,
            tol=magic.converge,
            constrain=True,
            debug=False,
            ):
        ''' Iterate to convergence
        '''
        cs = [self.eos.get_c().copy()]
        costs = [self.cost(cs[-1],debug=debug, key='initial')]
        tol *= abs(costs[-1])
        plot_data = []
        for i in range(max_it):
            cost, x = self.step(constrain=constrain)
            if debug:
                print('costs along line:\n{0}\n'.format(x))
            cost_ = self.cost(self.eos.get_c(), debug=debug, key=i)
            plot_data.append(x)
            costs.append(cost)
            cs.append(self.eos.get_c().copy())
            delta = costs[-2] - costs[-1]
            if delta < tol:
                if debug:
                    self.experiment['gun'].debug_plot(
                        None, None, show=True) # FixMe: For plt.show()
                if delta < 0:
                    self.eos.new_c(cs[-2])
                return
        return
    def cost(
            self,        # Opt instance
            c,           # Trial eos parameters
            debug=False, # Invoke plots of experiments
            key=''       # For debug plot traces
            ):
        ''' 
        '''
        rv = self.eos.log_prior(c)
        if debug:
            print('log_prior=    {0:4e}'.format(rv))
        for k in self.data.keys():
            exp = self.experiment[k]
            comparison = exp.compare(self.data[k], c)
            if debug and hasattr(exp, 'debug_plot'):
                exp.debug_plot(self.data[k], key)
            log_like = exp.log_like(*comparison) # FixMe: fix gun.Pq functions
            if debug:
                print('log_like({0})={1:4e}'.format(k, log_like))
            rv += log_like
        return -rv
def work():
    ''' This code for debugging stuff will change often
    '''
    return 0

def make_opt():
    import gun
    import eos
    nominal_eos = eos.Spline_eos(eos.Nominal())
    experiment = {'gun':gun.Gun(nominal_eos)}
    data = {'gun':gun.data()}
    return Opt(nominal_eos, experiment, data)
def test_init():
    make_opt()
    return 0
def test_step():
    make_opt().step()
    return 0
def test_fit():
    make_opt().fit(constrain=True, debug=True)
    return 0
def test():
    for name,value in globals().items():
        if not name.startswith('test_'):
            continue
        if value() == 0:
            print('{0} passed'.format(name))
        else:
            print('\nFAILED            {0}\n'.format(name))
    return 0
if __name__ == "__main__":
    import sys
    if len(sys.argv) >1 and sys.argv[1] == 'test':
        rv = test_fit()
        sys.exit(rv)
    if len(sys.argv) >1 and sys.argv[1] == 'work':
        sys.exit(work())
    main()

#---------------
# Local Variables:
# mode: python
# End:
