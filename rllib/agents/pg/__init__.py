from ray.rllib.algorithms.pg.pg import DEFAULT_CONFIG
from ray.rllib.algorithms.pg.pg import PG as PGTrainer
from ray.rllib.algorithms.pg.pg import PGConfig
from ray.rllib.algorithms.pg.pg_torch_policy import PGTorchPolicy
from ray.rllib.algorithms.pg.utils import post_process_advantages
from ray.rllib.utils.deprecation import deprecation_warning

__all__ = [
    "DEFAULT_CONFIG",
    "post_process_advantages",
    "PGConfig",
    "PGTorchPolicy",
    "PGTrainer",
]


deprecation_warning("ray.rllib.agents.pg", "ray.rllib.algorithms.pg", error=False)
