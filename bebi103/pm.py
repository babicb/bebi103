import numpy as np
import pandas as pd

import pymc3 as pm

def trace_to_df(trace, model=None, thin=1):
    """
    Convert a PyMC3 trace to a Pandas DataFrame

    To add: Compute logp for each point using model.logp().
    """
    # How many chains?
    chains = trace.chains
    data_len = len(trace.get_values(trace.varnames[0], thin=thin))
    
    # Set up chains as column in DataFrame
    chains = np.concatenate(
        [chain * np.ones(data_len // len(chains)) for chain in chains])
    df = pd.DataFrame(data={'chain': chains})

    # Add samples
    for var in trace.varnames:
        if len(var) < 2 or var[-2:] != '__':
            data = trace.get_values(var, thin=thin)
            if len(data.shape) == 1:
                df[var] = data
            else:
                for i in range(data.shape[1]):
                    df[var + '_' + str(i)] = data[:,i]

    # Convert chain to integer
    df['chain'] = df['chain'].astype(int)

    return df

def waic_no_diverging(trace):
    """
    Compute the WAIC taking out diverging samples.
    """
    pass


def Jeffreys(name, min_val=None, max_val=None, shape=None):
    """
    Create a Jeffreys prior for a scale parameter.

    Parameters
    ----------
    name : str
        Name of the variable.
    min_val : float, > 0
        Minimum value the variable can take.
    max_val : float, > `min_val`
        Maximum value the variable can take.
    shape: int or tuple of ints, default 1
        Shape of array of variables. If 1, then a single scalar.

    Returns
    -------
    output : pymc3 distribution
        Distribution for Jeffreys prior.
    """
    # Check inputs
    if type(name) != str:
        raise RuntimeError('`name` must be a string.')
    if min_val is None or max_val is None:
        raise RuntimeError('`min_val` and `max_val` must be provided.')
    if min_val <= 0:
        raise RuntimeError('`min_val` must be > 0.')
    if max_val <= min_val:
        raise RuntimeError('`max_val` must be > `min_val`.')

    # Set up Jeffreys prior
    if shape is None:
        log_var = pm.Uniform('log_' + name, 
                             lower=np.log(min_val), 
                             upper=np.log(max_val))
    else:
        log_var = pm.Uniform('log_' + name, 
                             lower=np.log(min_val), 
                             upper=np.log(max_val),
                             shape=shape)
    var = pm.Deterministic(name, pm.math.exp(log_var))

    return var


def ReparametrizedNormal(name, mu=None, sd=None, shape=1):
    """
    Create a reparametrized Normally distributed random variable.

    Parameters
    ----------
    name : str
        Name of the variable.
    mu : float
        Mean of Normal distribution.
    sd : float, > 0
        Standard deviation of Normal distribution.
    shape: int or tuple of ints, default 1
        Shape of array of variables. If 1, then a single scalar.

    Returns
    -------
    output : pymc3 distribution
        Distribution for a reparametrized Normal distribution.

    Notes
    -----
    .. The reparametrization procedure allows the sampler to sample
       a standard normal distribution, and then do a deterministic
       reparametrization to achieve sampling of the original desired 
       Normal distribution.
    """
    # Check inputs
    if type(name) != str:
        raise RuntimeError('`name` must be a string.')
    if mu is None or sd is None:
        raise RuntimeError('`mu` and `sd` must be provided.')

    var_reparam = pm.Normal(name + '_reparam', mu=0, sd=1, shape=shape)
    var = pm.Deterministic(name, mu + var_reparam * sd)

    return var


def ReparametrizedCauchy(name, alpha=None, beta=None, shape=1):
    """
    Create a reparametrized Cauchy distributed random variable.

    Parameters
    ----------
    name : str
        Name of the variable.
    alpha : float
        Mode of Cauchy distribution.
    beta : float, > 0
        Scale parameter of Cauchy distribution
    shape: int or tuple of ints, default 1
        Shape of array of variables. If 1, then a single scalar.

    Returns
    -------
    output : pymc3 distribution
        Reparametrized Cauchy distribution.

    Notes
    -----
    .. The reparametrization procedure allows the sampler to sample
       a Cauchy distribution with alpha = 0 and beta = 1, and then do a
       deterministic reparametrization to achieve sampling of the 
       original desired Cauchy distribution.
    """
    # Check inputs
    if type(name) != str:
        raise RuntimeError('`name` must be a string.')
    if alpha is None or beta is None:
        raise RuntimeError('`alpha` and `beta` must be provided.')

    var_reparam = pm.Cauchy(name + '_reparam', alpha=0, beta=1, shape=shape)
    var = pm.Deterministic(name, alpha + var_reparam * beta)

    return var
