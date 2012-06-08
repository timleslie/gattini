"""
Linear regression.
"""

import numarray as N
import numarray.linear_algebra as NL

def regress(X):
    """
    Apply a linear regression on X.

    X is an numarray array of form [Y|X].
    We split this up, do the regression and return the
    regression coefficients, beta_i.
    """
    X = N.array(X)
    Y = X[:,0].copy()
    X[:,0] = 1.0
    a = N.dot(NL.inverse(N.dot(N.transpose(X), X)), N.transpose(X))
    return N.dot(a, Y)
