from better_launch import BetterLaunch, launch_this
from moveit_configs_utils import MoveItConfigsBuilder

MOVEIT_PACKAGE = 'link6_moveit_config'
ROBOT_NAME = 'link6'


@launch_this(use_sim_time=True)
def kinova_link6_pick(object: str = 'apple'):
    moveit_configuration = (
        MoveItConfigsBuilder(ROBOT_NAME, package_name=MOVEIT_PACKAGE)
        .planning_pipelines(
            pipelines=['ompl', 'pilz_industrial_motion_planner'])
        .to_moveit_configs().to_dict())

    bl = BetterLaunch()
    bl.node(
        'robot_manipulation', 'kinova_link6_pick',
        name='pick_task',
        params={**moveit_configuration, 'object': object},
    )
