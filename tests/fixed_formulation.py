import os
import unittest
import warnings

import gurobipy as gp
import numpy as np
from gurobipy import GurobiError

from gurobi_ml import add_predictor_constr
from gurobi_ml.exceptions import NoSolution

VERBOSE = False


class FixedRegressionModel(unittest.TestCase):
    """Test that if we fix the input of the predictor the feasible solution from
    Gurobi is identical to what the predict function would return."""

    def setUp(self) -> None:
        self.rng = np.random.default_rng(1)

    def fixed_model(self, predictor, examples, nonconvex, **kwargs):
        params = {
            "OutputFlag": 0,
            "NonConvex": 2,
        }
        for param in params:
            try:
                params[param] = int(params[param])
            except ValueError:
                pass

        with gp.Env(params=params) as env, gp.Model(env=env) as gpm:
            x = gpm.addMVar(examples.shape, lb=examples - 1e-4, ub=examples + 1e-4)

            pred_constr = add_predictor_constr(gpm, predictor, x, **kwargs)

            y = pred_constr.output

            self.additional_test(predictor, pred_constr)
            with self.assertRaises(NoSolution):
                pred_constr.get_error()
            with open(os.devnull, "w") as outnull:
                pred_constr.print_stats(file=outnull)
            try:
                gpm.optimize()
            except GurobiError as E:
                if E.errno == 10010:
                    warnings.warn(UserWarning("Limited license"))
                    self.skipTest("Model too large for limited license")
                else:
                    raise

            if nonconvex:
                tol = 5e-3
            else:
                tol = 1e-5
            vio = gpm.MaxVio
            if vio > 1e-5:
                warnings.warn(UserWarning(f"Big solution violation {vio}"))
                warnings.warn(UserWarning(f"predictor {predictor}"))
            tol = max(tol, vio)
            tol *= np.max(y.X)
            abserror = pred_constr.get_error().astype(float)
            if (abserror > tol).any():
                print(f"Error: {y.X} != {predictor.predict(examples)}")

            self.assertLessEqual(np.max(abserror), tol)

    def do_one_case(self, one_case, X, n_sample, combine, **kwargs):
        choice = self.rng.integers(X.shape[0], size=n_sample)
        examples = X[choice, :]
        if combine == "all":
            # Do the average case
            examples = (examples.sum(axis=0) / n_sample).reshape(1, -1) - 1e-2
        elif combine == "pairs":
            # Make pairwise combination of the examples
            even_rows = examples[::2, :]
            odd_rows = examples[1::2, :]
            assert odd_rows.shape == even_rows.shape
            examples = (even_rows + odd_rows) / 2.0 - 1e-2
            assert examples.shape == even_rows.shape

        predictor = one_case["predictor"]
        with super().subTest(
            regressor=predictor, exampleno=choice, n_sample=n_sample, combine=combine
        ):
            if VERBOSE:
                print(f"Doing {predictor} with example {choice}")
            self.fixed_model(predictor, examples, one_case["nonconvex"], **kwargs)
