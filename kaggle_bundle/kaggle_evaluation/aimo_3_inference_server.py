import kaggle_evaluation.core.templates
from . import aimo_3_gateway

class AIMO3InferenceServer(kaggle_evaluation.core.templates.InferenceServer):
    def __init__(self, predict_fn):
        super().__init__(predict_fn)

    def _get_gateway_for_test(self, data_paths=None, *args, **kwargs):
        return aimo_3_gateway.AIMO3Gateway(data_paths)
