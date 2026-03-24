import os
from collections.abc import Generator
import kaggle_evaluation.core.templates
import polars as pl
from kaggle_evaluation.core.base_gateway import (
    GatewayRuntimeError,
    GatewayRuntimeErrorType,
)

USE_PRIVATE_SET = False

class AIMO3Gateway(kaggle_evaluation.core.templates.Gateway):
    def __init__(self, data_paths: tuple[str] | None = None):
        super().__init__(data_paths, file_share_dir=None)
        self.data_paths = data_paths
        self.set_response_timeout_seconds(60 * 60 * 9)
        self.row_id_column_name = 'id'
        self.target_column_name = 'answer'

    def unpack_data_paths(self):
        if not self.data_paths:
            self.test_path = '/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.csv'
        else:
            self.test_path = self.data_paths[0]

    def generate_data_batches(
        self,
    ) -> Generator[tuple[pl.DataFrame, pl.DataFrame], None, None]:
        random_seed = int.from_bytes(os.urandom(4), byteorder='big')
        if not os.path.exists(self.test_path):
            # Fallback for local testing
            test = pl.read_csv('reference.csv')
        else:
            test = pl.read_csv(self.test_path)

        if not USE_PRIVATE_SET:
            test = test.sample(fraction=1.0, shuffle=True, with_replacement=False, seed=random_seed)
        for row in test.iter_slices(n_rows=1):
            yield row, row.select('id')

    def competition_specific_validation(self, prediction_batch, row_ids, data_batch) -> None:
        pass
