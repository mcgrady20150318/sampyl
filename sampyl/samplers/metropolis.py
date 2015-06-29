from ..core import np
from .base import Sampler


class Metropolis(Sampler):
    # TODO: Allow for sticking in different proposal distributions.
    _grad_logp_flag = False

    def __init__(self, logp, start=None, scale=1., tune_interval=100):
        """ Metropolis-Hastings sampler for drawing from a distribution 
            defined by a logp function.

            Has automatic scaling such that acceptance rate stays around 50%

            Parameters
            ----------

            logp: function
                log P(X) function for sampling distribution
            start: scalar or 1D array-like
                starting state for sampler
            scale: scalar or 1D array-like
                initial scaling factor for proposal distribution
            tune_interval: int 
                number of samples between tunings of scale factor

        """
        super().__init__(logp, None, start=start, scale=scale)
        self.tune_interval = tune_interval
        self._steps_until_tune = tune_interval
        self._accepted = 0

    def step(self):
        """ Perform a Metropolis-Hastings step. """
        x = self.state
        y = proposal(x, scale=self.scale)
        if accept(x, y, self.logp):
            self.state = y
            self._accepted += 1

        self._sampled += 1

        self._steps_until_tune -= 1
        if self._steps_until_tune == 0:
            self.scale = tune(self.scale, self.acceptance)
            self._steps_until_tune = self.tune_interval

        return self.state

    @property
    def acceptance(self):
        return self._accepted/self._sampled

    def __repr__(self):
        return 'Metropolis-Hastings sampler'


def proposal(state, scale=1.):
    """ Sample a proposal x from a multivariate normal distribution. """
    y = []
    for i, var in enumerate(state):
        try:
            size = var.shape
        except AttributeError:
            size = 1.
        y.append(np.random.normal(var, scale[i]))
    return np.array(y)


def accept(x, y, logp):
    """ Return a boolean indicating if the proposed sample should be accepted,
        given the logp ratio logp(y)/logp(x).
    """
    delp = logp(*y) - logp(*x)

    if np.isfinite(delp) and np.log(np.random.uniform()) < delp:
        return True
    else:
        return False


def tune(scale, acceptance):
    """ Borrowed from PyMC3 """

    # Switch statement
    if acceptance < 0.001:
        # reduce by 90 percent
        scale *= 0.1
    elif acceptance < 0.05:
        # reduce by 50 percent
        scale *= 0.5
    elif acceptance < 0.2:
        # reduce by ten percent
        scale *= 0.9
    elif acceptance > 0.95:
        # increase by factor of ten
        scale *= 10.0
    elif acceptance > 0.75:
        # increase by double
        scale *= 2.0
    elif acceptance > 0.5:
        # increase by ten percent
        scale *= 1.1

    return scale