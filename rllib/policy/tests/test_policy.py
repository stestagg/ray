import unittest

import ray
from ray.rllib.algorithms.dqn import DEFAULT_CONFIG, DQN
from ray.rllib.utils.test_utils import check, framework_iterator


class TestPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        ray.init()

    @classmethod
    def tearDownClass(cls) -> None:
        ray.shutdown()

    def test_policy_save_restore(self):
        config = DEFAULT_CONFIG.copy()
        for _ in framework_iterator(config):
            algo = DQN(config=config, env="CartPole-v0")
            policy = algo.get_policy()
            state1 = policy.get_state()
            algo.train()
            state2 = policy.get_state()
            check(
                state1["_exploration_state"]["last_timestep"],
                state2["_exploration_state"]["last_timestep"],
                false=True,
            )
            check(state1["global_timestep"], state2["global_timestep"], false=True)
            # Reset policy to its original state and compare.
            policy.set_state(state1)
            state3 = policy.get_state()
            # Make sure everything is the same.
            check(state1, state3)


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", __file__]))
