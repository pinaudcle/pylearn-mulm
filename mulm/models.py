# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 13:25:41 2013

@author: ed203246
"""
import scipy
import numpy as np
from sklearn.preprocessing import scale
from scipy import stats


class MUPairwiseCorr:
    """Mass-univariate pairwise correlations. Given two arrays X [n_samples x p]
    and Y [n_samples x q]. Fit p x q independent linear models. Prediction
    and stats return [p x q] array.


    Example
    -------
    >>> import numpy as np
    >>> from mulm import MUPairwiseCorr
    >>> X = np.random.randn(10, 5)
    >>> Y = np.random.randn(10, 3)
    >>> corr = MUPairwiseCorr()
    >>> corr.fit(X, Y)
    <mulm.models.MUPairwiseCorr instance at 0x30da878>
    >>> f, p = corr.stats_f(X, Y)
    >>> print f.shape
    (5, 3)
    """
    def __init__(self, **kwargs):
        pass

    def fit(self, X, Y):
        Xs = scale(X, copy=True)
        Ys = scale(Y, copy=True)
        self.n_samples = X.shape[0]
        self.Corr_ = np.dot(Xs.T, Ys) / self.n_samples
        return self

    def predict(self, X):
        pass

    def stats_f(self, pval=True):
        R2 = self.Corr_ ** 2
        df_res = self.n_samples - 2
        f_stats = R2 * df_res / (1 - R2)
        if not pval:
            return (f_stats, None)
        else:
            p_vals = stats.f.sf(f_stats, 1, df_res)
            return f_stats, p_vals

class MUOLS:
    """Mass-univariate linear modeling based Ordinary Least Squares.
    Given two arrays X [n_samples x p] and Y [n_samples x q].
    Fit q independent linear models. Prediction and stats return [p x q] array.
    Fit independant OLS models for each columns of Y.

    Example
    -------
    >>> import numpy as np
    >>> import mulm
    >>> n_samples = 10
    >>> X = np.random.randn(n_samples, 5)
    >>> X[:, -1] = 1  # Add intercept
    >>> Y = np.random.randn(n_samples, 4)
    >>> betas = np.array([1, 2, 2, 0, 3])
    >>> Y[:, 0] += np.dot(X, betas)
    >>> Y[:, 1] += np.dot(X, betas)
    >>> linreg = mulm.MUOLS()
    >>> linreg.fit(X, Y)
    >>> Ypred = linreg.predict(X)
    >>> ss_errors = np.sum((Y - Ypred) ** 2, axis=0)
    linreg.stats_f_coefficients(X, Y)
    """
    def __init__(self, **kwargs):
        self.coef_ = None

    def fit(self, X, Y):
        from sklearn.utils import safe_asarray
        X = safe_asarray(X)
        Y = safe_asarray(Y)
        self.coef_ = np.dot(np.linalg.pinv(X), Y)  # USE SCIPY ??
        # Ypred = self.predict(X)
        # self.coef_ = np.dot(scipy.linalg.pinv(X), Y)
        # self.coef_ = np.ones(X.shape[1])
        return self

    def predict(self, X):
        from sklearn.utils import safe_asarray
        import numpy as np
        X = safe_asarray(X)
        pred_y = np.dot(X, self.coef_)
        return pred_y

#    def stats_t_predictions(self, X, contrast, pval=True):
#        """Return Two array tvales and pvalues of shape []"""
#        ##Ypred = self.predict(X)
#        #ss_errors = np.sum((Y - Ypred) ** 2, axis=0)
#        tval, pvalt = self.ols_stats_tcon(X, self.ss_errors_, contrast,
#                                          pval)
#        return tval, pvalt

    def stats_t_coefficients(self, X, Y, contrast, pval=False):
        """Compute statistics (t-scores and p-value associated to contrast)

        Parameters
        ----------

        X 2-d array

        Y 2-d array

        contrast  1-d array

        pval: boolean
            compute pval

        ret_df: boolean
            return pval

        Return
        ------
        tstats, pvals, df

        Example
        -------
        >>> import numpy as np
        >>> n_samples = 10
        >>> X = np.random.randn(n_samples, 5)
        >>> X[:, -1] = 1  # Add intercept
        >>> Y = np.random.randn(n_samples, 4)
        >>> betas = np.array([1, 2, 2, 0, 3])
        >>> Y[:, 0] += np.dot(X, betas)
        >>> Y[:, 1] += np.dot(X, betas)
        >>> 
        >>> betas, ss_errors = mulm.ols(X, Y)
        >>> p, t = mulm.ols_stats_tcon(X, betas, ss_errors, contrast=[1, 0, 0, 0, 0], pval=True)
        >>> p, f = mulm.ols_stats_fcon(X, betas, ss_errors, contrast=[1, 0, 0, 0, 0], pval=True)
        """
        from scipy import stats
        import numpy as np
        Ypred = self.predict(X)
        betas = self.coef_
        ss_errors = np.sum((Y - Ypred) ** 2, axis=0)
        ccontrast = np.asarray(contrast)
        n = X.shape[0]
        # t = c'beta / std(c'beta)
        # std(c'beta) = sqrt(var_err (c'X+)(X+'c))
        Xpinv = scipy.linalg.pinv(X)
        cXpinv = np.dot(ccontrast, Xpinv)
        R = np.eye(n) - np.dot(X, Xpinv)
        df = np.trace(R)
        ## Broadcast over ss errors
        var_errors = ss_errors / df
        std_cbeta = np.sqrt(var_errors * np.dot(cXpinv, cXpinv.T))
        t_stats = np.dot(ccontrast, betas) / std_cbeta
        p_vals = stats.t.sf(t_stats, df) if pval else None
        return t_stats, p_vals, df
        
    def stats_f_coefficients(self, X, Y, contrast, pval=False):
        from sklearn.utils import array2d
        Ypred = self.predict(X)
        betas = self.coef_
        ss_errors = np.sum((Y - Ypred) ** 2, axis=0)
        C1 = array2d(contrast).T
        n = X.shape[0]
        p = X.shape[1]
        Xpinv = scipy.linalg.pinv(X)
        rank_x = np.linalg.matrix_rank(Xpinv)
        C0 = np.eye(p) - np.dot(C1, scipy.linalg.pinv(C1))  # Ortho. cont. to C1
        X0 = np.dot(X, C0)  # Design matrix of the reduced model
        X0pinv = scipy.linalg.pinv(X0)
        rank_x0 = np.linalg.matrix_rank(X0pinv)
        # Find the subspace (X1) of Xc1, which is orthogonal to X0
        # The projection matrix M due to X1 can be derived from the residual
        # forming matrix of the reduced model X0
        # R0 is the residual forming matrix of the reduced model
        R0 = np.eye(n) - np.dot(X0, X0pinv)
        # R is the residual forming matrix of the full model
        R = np.eye(n) - np.dot(X, Xpinv)
        # compute the projection matrix
        M = R0 - R
        Ypred = np.dot(X, betas)
        SS = np.sum(Ypred * np.dot(M, Ypred), axis=0)
        df_c1 = rank_x - rank_x0
        df_res = n - rank_x
        ## Broadcast over ss_errors of Y
        f_stats = (SS * df_res) / (ss_errors * df_c1)
        if not pval:
            return (f_stats, None)
        else:
            p_vals = stats.f.sf(f_stats, df_c1, df_res)
            return f_stats, p_vals


class MUOLSStatsCoefficients(MUOLS):
    """Statistics on coefficients of MUOLS models. for each OLS fitted model compute
    t-scores and p-values for fitted coeficients"""
    def __init__(self, **kwargs):
        MUOLS.__init__(self)#**kwargs)

    def stats(self, X, Y):
        if self.coef_ is None:
            raise ValueError("Model has not been fitted yet, call fit(X, Y)")
        #X = np.random.randn(100, 2)
        #Y = np.hstack([np.dot(X, [1, 2])[:, np.newaxis], np.random.randn(100, 3)])
        pvals = list()
        tvals = list()
        dfs = list()
        for j in xrange(X.shape[1]):
            contrast = np.zeros(X.shape[1])
            contrast[j] += 1
            t, p, df= self.stats_t_coefficients(X, Y, contrast=contrast, pval=True)
            tvals.append(t)
            pvals.append(p)
            dfs.append(df)
        pvals = np.asarray(pvals)
        tvals = np.asarray(tvals)
        dfs =  np.asarray(dfs)
        # "transform" should return a dictionary
        return tvals, pvals, dfs


#class MUOLSStatsPredictions:
#    """Statistics on coefficients of MUOLS models. for each OLS fitted model compute
#    r2-score (explain variance) and p-values for prediction.
#    See example in ./examples/permutations.py
#    """
#
#    def __init__(self):
#        self.muols = MUOLS()
#
#    def transform(self, X, Y):
#        # definition of Explained Variation of R2
#        # http://www.stat.columbia.edu/~gelman/research/published/rsquared.pdf
#        import scipy
#        self.muols.fit(X, Y)
#        Ypred = self.muols.predict(X)
#        var_epsilon = scipy.var(Y - Ypred, axis=0)
#        var_Y = scipy.var(Y, axis=0)
#        r2 = 1.0 - var_epsilon / var_Y
#        return {"r2": r2}
#
#
#class MURidgeLM:
#    """Mass-univariate linear modeling based on Ridge regression.
#    Fit independant Ridge models for each columns of Y."""
#
#    def __init__(self, **kwargs):
#        pass
#
#    def fit(self, X, Y):
#        pass
#
#    def predict(self, X):
#        pass
