import warnings
from abc import ABCMeta
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from ray.util.annotations import DeveloperAPI, PublicAPI
from ray.util.ml_utils.checkpoint_manager import _TrackedCheckpoint

if TYPE_CHECKING:
    from ray.tune.stopper import Stopper
    from ray.tune.trial import Trial


class _CallbackMeta(ABCMeta):
    """A helper metaclass to ensure container classes (e.g. CallbackList) have
    implemented all the callback methods (e.g. `on_*`).
    """

    def __new__(mcs, name: str, bases: Tuple[type], attrs: Dict[str, Any]) -> type:
        cls = super().__new__(mcs, name, bases, attrs)

        if mcs.need_check(cls, name, bases, attrs):
            mcs.check(cls, name, bases, attrs)

        return cls

    @classmethod
    def need_check(
        mcs, cls: type, name: str, bases: Tuple[type], attrs: Dict[str, Any]
    ) -> bool:

        return attrs.get("IS_CALLBACK_CONTAINER", False)

    @classmethod
    def check(
        mcs, cls: type, name: str, bases: Tuple[type], attrs: Dict[str, Any]
    ) -> None:

        methods = set()
        for base in bases:
            methods.update(
                attr_name
                for attr_name, attr in vars(base).items()
                if mcs.need_override_by_subclass(attr_name, attr)
            )
        overridden = {
            attr_name
            for attr_name, attr in attrs.items()
            if mcs.need_override_by_subclass(attr_name, attr)
        }
        missing = methods.difference(overridden)
        if missing:
            raise TypeError(
                f"Found missing callback method: {missing} "
                f"in class {cls.__module__}.{cls.__qualname__}."
            )

    @classmethod
    def need_override_by_subclass(mcs, attr_name: str, attr: Any) -> bool:
        return (
            (
                attr_name.startswith("on_")
                and not attr_name.startswith("on_trainer_init")
            )
            or attr_name == "setup"
        ) and callable(attr)


@PublicAPI(stability="beta")
class Callback(metaclass=_CallbackMeta):
    """Tune base callback that can be extended and passed to a ``TrialRunner``

    Tune callbacks are called from within the ``TrialRunner`` class. There are
    several hooks that can be used, all of which are found in the submethod
    definitions of this base class.

    The parameters passed to the ``**info`` dict vary between hooks. The
    parameters passed are described in the docstrings of the methods.

    This example will print a metric each time a result is received:

    .. code-block:: python

        from ray import tune
        from ray.tune import Callback


        class MyCallback(Callback):
            def on_trial_result(self, iteration, trials, trial, result,
                                **info):
                print(f"Got result: {result['metric']}")


        def train(config):
            for i in range(10):
                tune.report(metric=i)


        tune.run(
            train,
            callbacks=[MyCallback()])

    """

    # arguments here match Experiment.public_spec
    def setup(
        self,
        stop: Optional["Stopper"] = None,
        num_samples: Optional[int] = None,
        total_num_samples: Optional[int] = None,
        **info,
    ):
        """Called once at the very beginning of training.

        Any Callback setup should be added here (setting environment
        variables, etc.)

        Arguments:
            stop: Stopping criteria.
                If ``time_budget_s`` was passed to ``tune.run``, a
                ``TimeoutStopper`` will be passed here, either by itself
                or as a part of a ``CombinedStopper``.
            num_samples: Number of times to sample from the
                hyperparameter space. Defaults to 1. If `grid_search` is
                provided as an argument, the grid will be repeated
                `num_samples` of times. If this is -1, (virtually) infinite
                samples are generated until a stopping condition is met.
            total_num_samples: Total number of samples factoring
                in grid search samplers.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_step_begin(self, iteration: int, trials: List["Trial"], **info):
        """Called at the start of each tuning loop step.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_step_end(self, iteration: int, trials: List["Trial"], **info):
        """Called at the end of each tuning loop step.

        The iteration counter is increased before this hook is called.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_trial_start(
        self, iteration: int, trials: List["Trial"], trial: "Trial", **info
    ):
        """Called after starting a trial instance.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            trial: Trial that just has been started.
            **info: Kwargs dict for forward compatibility.

        """
        pass

    def on_trial_restore(
        self, iteration: int, trials: List["Trial"], trial: "Trial", **info
    ):
        """Called after restoring a trial instance.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            trial: Trial that just has been restored.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_trial_save(
        self, iteration: int, trials: List["Trial"], trial: "Trial", **info
    ):
        """Called after receiving a checkpoint from a trial.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            trial: Trial that just saved a checkpoint.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_trial_result(
        self,
        iteration: int,
        trials: List["Trial"],
        trial: "Trial",
        result: Dict,
        **info,
    ):
        """Called after receiving a result from a trial.

        The search algorithm and scheduler are notified before this
        hook is called.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            trial: Trial that just sent a result.
            result: Result that the trial sent.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_trial_complete(
        self, iteration: int, trials: List["Trial"], trial: "Trial", **info
    ):
        """Called after a trial instance completed.

        The search algorithm and scheduler are notified before this
        hook is called.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            trial: Trial that just has been completed.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_trial_error(
        self, iteration: int, trials: List["Trial"], trial: "Trial", **info
    ):
        """Called after a trial instance failed (errored).

        The search algorithm and scheduler are notified before this
        hook is called.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            trial: Trial that just has errored.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_checkpoint(
        self,
        iteration: int,
        trials: List["Trial"],
        trial: "Trial",
        checkpoint: _TrackedCheckpoint,
        **info,
    ):
        """Called after a trial saved a checkpoint with Tune.

        Arguments:
            iteration: Number of iterations of the tuning loop.
            trials: List of trials.
            trial: Trial that just has errored.
            checkpoint: Checkpoint object that has been saved
                by the trial.
            **info: Kwargs dict for forward compatibility.
        """
        pass

    def on_experiment_end(self, trials: List["Trial"], **info):
        """Called after experiment is over and all trials have concluded.

        Arguments:
            trials: List of trials.
            **info: Kwargs dict for forward compatibility.
        """
        pass


@DeveloperAPI
class CallbackList(Callback):
    """Call multiple callbacks at once."""

    IS_CALLBACK_CONTAINER = True

    def __init__(self, callbacks: List[Callback]):
        self._callbacks = callbacks

    def setup(self, **info):
        for callback in self._callbacks:
            try:
                callback.setup(**info)
            except TypeError as e:
                if "argument" in str(e):
                    warnings.warn(
                        "Please update `setup` method in callback "
                        f"`{callback.__class__}` to match the method signature"
                        " in `ray.tune.callback.Callback`.",
                        FutureWarning,
                    )
                    callback.setup()
                else:
                    raise e

    def on_step_begin(self, **info):
        for callback in self._callbacks:
            callback.on_step_begin(**info)

    def on_step_end(self, **info):
        for callback in self._callbacks:
            callback.on_step_end(**info)

    def on_trial_start(self, **info):
        for callback in self._callbacks:
            callback.on_trial_start(**info)

    def on_trial_restore(self, **info):
        for callback in self._callbacks:
            callback.on_trial_restore(**info)

    def on_trial_save(self, **info):
        for callback in self._callbacks:
            callback.on_trial_save(**info)

    def on_trial_result(self, **info):
        for callback in self._callbacks:
            callback.on_trial_result(**info)

    def on_trial_complete(self, **info):
        for callback in self._callbacks:
            callback.on_trial_complete(**info)

    def on_trial_error(self, **info):
        for callback in self._callbacks:
            callback.on_trial_error(**info)

    def on_checkpoint(self, **info):
        for callback in self._callbacks:
            callback.on_checkpoint(**info)

    def on_experiment_end(self, **info):
        for callback in self._callbacks:
            callback.on_experiment_end(**info)
