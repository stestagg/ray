"""Test the collective group APIs."""
import pytest

import ray
from ray.util.collective.tests.cpu_util import Worker, create_collective_workers
from ray.util.collective.types import Backend


@pytest.mark.parametrize("backend", [Backend.GLOO])
@pytest.mark.parametrize("group_name", ["default", "test", "123?34!"])
def test_init_two_actors(ray_start_single_node, group_name, backend):
    world_size = 2
    actors, results = create_collective_workers(world_size, group_name, backend=backend)
    for i in range(world_size):
        assert results[i]


@pytest.mark.parametrize("backend", [Backend.GLOO])
def test_init_multiple_groups(ray_start_single_node, backend):
    world_size = 2
    num_groups = 10
    actors = [Worker.remote() for i in range(world_size)]
    for i in range(num_groups):
        group_name = str(i)
        init_results = ray.get(
            [
                actor.init_group.remote(
                    world_size, k, group_name=group_name, backend=backend
                )
                for k, actor in enumerate(actors)
            ]
        )
        for j in range(world_size):
            assert init_results[j]


@pytest.mark.parametrize("backend", [Backend.GLOO])
def test_get_rank(ray_start_single_node, backend):
    world_size = 2
    actors, _ = create_collective_workers(world_size, backend=backend)
    actor0_rank = ray.get(actors[0].report_rank.remote())
    assert actor0_rank == 0
    actor1_rank = ray.get(actors[1].report_rank.remote())
    assert actor1_rank == 1

    # create a second group with a different name,
    # and different order of ranks.
    new_group_name = "default2"
    ray.get(
        [
            actor.init_group.remote(
                world_size,
                world_size - 1 - i,
                group_name=new_group_name,
                backend=backend,
            )
            for i, actor in enumerate(actors)
        ]
    )
    actor0_rank = ray.get(actors[0].report_rank.remote(new_group_name))
    assert actor0_rank == 1
    actor1_rank = ray.get(actors[1].report_rank.remote(new_group_name))
    assert actor1_rank == 0


@pytest.mark.parametrize("backend", [Backend.GLOO])
def test_get_world_size(ray_start_single_node, backend):
    world_size = 2
    actors, _ = create_collective_workers(world_size, backend=backend)
    actor0_world_size = ray.get(actors[0].report_world_size.remote())
    actor1_world_size = ray.get(actors[1].report_world_size.remote())
    assert actor0_world_size == actor1_world_size == world_size


@pytest.mark.parametrize("backend", [Backend.GLOO])
def test_is_group_initialized(ray_start_single_node, backend):
    world_size = 2
    actors, _ = create_collective_workers(world_size, backend=backend)
    # check group is_init
    actor0_is_init = ray.get(actors[0].report_is_group_initialized.remote())
    assert actor0_is_init
    actor0_is_init = ray.get(actors[0].report_is_group_initialized.remote("random"))
    assert not actor0_is_init
    actor0_is_init = ray.get(actors[0].report_is_group_initialized.remote("123"))
    assert not actor0_is_init
    actor1_is_init = ray.get(actors[0].report_is_group_initialized.remote())
    assert actor1_is_init
    actor1_is_init = ray.get(actors[0].report_is_group_initialized.remote("456"))
    assert not actor1_is_init


@pytest.mark.parametrize("backend", [Backend.GLOO])
def test_destroy_group(ray_start_single_node, backend):
    world_size = 2
    actors, _ = create_collective_workers(world_size, backend=backend)
    # Now destroy the group at actor0
    ray.wait([actors[0].destroy_group.remote()])
    actor0_is_init = ray.get(actors[0].report_is_group_initialized.remote())
    assert not actor0_is_init

    # should go well as the group `random` does not exist at all
    ray.wait([actors[0].destroy_group.remote("random")])

    actor1_is_init = ray.get(actors[1].report_is_group_initialized.remote())
    assert actor1_is_init
    ray.wait([actors[1].destroy_group.remote("random")])
    actor1_is_init = ray.get(actors[1].report_is_group_initialized.remote())
    assert actor1_is_init
    ray.wait([actors[1].destroy_group.remote("default")])
    actor1_is_init = ray.get(actors[1].report_is_group_initialized.remote())
    assert not actor1_is_init

    # Now reconstruct the group using the same name
    init_results = ray.get(
        [actor.init_group.remote(world_size, i) for i, actor in enumerate(actors)]
    )
    for i in range(world_size):
        assert init_results[i]
    actor0_is_init = ray.get(actors[0].report_is_group_initialized.remote())
    assert actor0_is_init
    actor1_is_init = ray.get(actors[0].report_is_group_initialized.remote())
    assert actor1_is_init


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", "-x", __file__]))
