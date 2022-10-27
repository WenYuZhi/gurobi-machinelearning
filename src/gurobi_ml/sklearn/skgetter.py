# Copyright © 2022 Gurobi Optimization, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

import warnings

from sklearn.utils.validation import check_is_fitted

from ..exceptions import NoSolution


class SKgetter:
    """Base class for all sklearn convertors

    Class used to implement some common functionalities

    Attributes
    ----------
    predictor
        Scikit-Learn predictor embedded into Gurobi model.
    """

    def __init__(self, predictor, output_type="regular", **kwargs):
        check_is_fitted(predictor)
        self.predictor = predictor
        self.output_type = output_type
        try:
            self.n_outputs_ = predictor.n_outputs_
        except AttributeError:
            pass

    def get_error(self):
        """Returns error in Gurobi's solution with respect to prediction from input

        Returns
        -------
        float
            Assuming that we have a solution for the input and output variables
            `x, y`. Returns the difference between `predict(x)` and
            `y`, where predict is the corresponding function for the Scikit-Learn
            object we are modeling.

        Raises
        ------
        NoSolution
            If the Gurobi model has no solution (either was not optimized or is infeasible).
        """
        if self._has_solution():
            if self.output_type == "probability_1":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    predicted = self.predictor.predict_proba(self.input.X)[:, 1]
            elif self.output_type == "probability":
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    predicted = self.predictor.predict_proba(self.input.X)
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=UserWarning)
                    predicted = self.predictor.predict(self.input.X)
            if len(predicted.shape) == 1:
                predicted = predicted.reshape(-1, 1)
            return predicted - self.output.X
        raise NoSolution()
