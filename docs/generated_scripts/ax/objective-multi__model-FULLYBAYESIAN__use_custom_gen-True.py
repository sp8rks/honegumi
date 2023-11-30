from ax.modelbridge.factory import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from ax.service.ax_client import AxClient
from ax.service.utils.instantiation import ObjectiveProperties
from ax.utils.measurement.synthetic_functions import branin

obj1_name = "branin"
obj2_name = "neg_branin"


def branin_moo(x1, x2):
    """Multi-objective branin function

    The first objective is the normal branin value and the second
    objective is the negative branin value.
    """
    return {obj1_name: branin(x1, x2), obj2_name: -branin(x1, x2)}


gs = GenerationStrategy(
    steps=[
        GenerationStep(
            model=Models.SOBOL,
            num_trials=5,
            min_trials_observed=3,
            max_parallelism=5,
            model_kwargs={"seed": 999},
            model_gen_kwargs={},
        ),
        GenerationStep(
            model=Models.FULLYBAYESIAN,
            num_trials=-1,
            max_parallelism=3,
        ),
    ]
)

ax_client = AxClient(generation_strategy=gs)
ax_client.create_experiment(
    parameters=[
        {"name": "x1", "type": "range", "bounds": [-5.0, 10.0]},
        {"name": "x2", "type": "range", "bounds": [0.0, 10.0]},
    ],
    objectives={
        obj1_name: ObjectiveProperties(minimize=True, threshold=None),
        obj2_name: ObjectiveProperties(minimize=True, threshold=None),
    },
)


for _ in range(15):
    parameters, trial_index = ax_client.get_next_trial()
    results = branin_moo(parameters["x1"], parameters["x2"])
    ax_client.complete_trial(trial_index=trial_index, raw_data=results)

pareto_results = ax_client.get_pareto_optimal_parameters()
