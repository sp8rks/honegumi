import numpy as np
from ax.modelbridge.factory import Models
from ax.modelbridge.generation_strategy import GenerationStep, GenerationStrategy
from ax.service.ax_client import AxClient, ObjectiveProperties

obj1_name = "branin"
obj2_name = "branin_swapped"


def branin_moo(x1, x2, c1):
    y = float(
        (x2 - 5.1 / (4 * np.pi**2) * x1**2 + 5.0 / np.pi * x1 - 6.0) ** 2
        + 10 * (1 - 1.0 / (8 * np.pi)) * np.cos(x1)
        + 10
    )

    # add a made-up penalty based on category
    penalty_lookup = {"A": 1.0, "B": 0.0, "C": 2.0}
    y += penalty_lookup[c1]

    # second objective has x1 and x2 swapped
    y2 = float(
        (x1 - 5.1 / (4 * np.pi**2) * x2**2 + 5.0 / np.pi * x2 - 6.0) ** 2
        + 10 * (1 - 1.0 / (8 * np.pi)) * np.cos(x2)
        + 10
    )

    # add a made-up penalty based on category
    penalty_lookup = {"A": 0.0, "B": 2.0, "C": 1.0}
    y2 += penalty_lookup[c1]

    return {obj1_name: y, obj2_name: y2}


gs = GenerationStrategy(
    steps=[
        GenerationStep(
            model=Models.SOBOL,
            num_trials=6,  # https://github.com/facebook/Ax/issues/922
            min_trials_observed=3,
            max_parallelism=5,
            model_kwargs={"seed": 999},
            model_gen_kwargs={},
        ),
        GenerationStep(
            model=Models.FULLYBAYESIANMOO,
            num_trials=-1,
            max_parallelism=3,
            model_kwargs={},
        ),
    ]
)

ax_client = AxClient(generation_strategy=gs)

ax_client.create_experiment(
    parameters=[
        {"name": "x1", "type": "range", "bounds": [-5.0, 10.0]},
        {"name": "x2", "type": "range", "bounds": [0.0, 10.0]},
        {
            "name": "c1",
            "type": "choice",
            "is_ordered": False,
            "values": ["A", "B", "C"],
        },
    ],
    objectives={
        obj1_name: ObjectiveProperties(minimize=True, threshold=25.0),
        obj2_name: ObjectiveProperties(minimize=True, threshold=15.0),
    },
    parameter_constraints=[
        "x1 <= x2",  # example of an order constraint
        "1.0*x1 + 0.5*x2 <= 15.0",  # example of a linear constraint. Note the lack of space around the asterisks
    ],
)


batch_size = 2


for _ in range(21):

    parameterizations, optimization_complete = ax_client.get_next_trials(batch_size)
    for trial_index, parameterization in list(parameterizations.items()):
        # extract parameters
        x1 = parameterization["x1"]
        x2 = parameterization["x2"]

        c1 = parameterization["c1"]

        results = branin_moo(x1, x2, c1)
        ax_client.complete_trial(trial_index=trial_index, raw_data=results)

pareto_results = ax_client.get_pareto_optimal_parameters()
