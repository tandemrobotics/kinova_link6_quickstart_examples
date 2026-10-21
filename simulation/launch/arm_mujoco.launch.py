import os
import tempfile

from better_launch import BetterLaunch, launch_this
from better_launch.convenience import (
    read_robot_description,
    robot_state_publisher,
    spawn_controller,
)


def write_rendered_scene_file():
    apple_assets_directory = os.path.abspath(
        'simulation/models/ycb/013_apple/google_16k')
    with open(os.path.abspath(
            'manipulation/config/mujoco_scene.xml')) as template:
        scene = template.read().replace(
            '${APPLE_ASSETS}', apple_assets_directory)
    scene_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.xml', delete=False)
    scene_file.write(scene)
    scene_file.close()
    return scene_file.name


DESCRIPTION_PACKAGE = 'link6_description'
CONTROL_PACKAGE = 'link6_control'
MOVEIT_PACKAGE = 'link6_moveit_config'
ROBOT_NAME = 'link6'
GRIPPER = 'robotiq_2f_85'


@launch_this(use_sim_time=True)
def arm_mujoco_simulation():
    install_directory = os.path.abspath('install')
    os.environ.pop('ZENOH_CONFIG_OVERRIDE', None)
    os.environ.pop('ZENOH_SESSION_CONFIG_URI', None)

    bl = BetterLaunch()
    bl.process(
        os.path.join(
            os.environ['CONDA_PREFIX'], 'lib', 'rmw_zenoh_cpp', 'rmw_zenohd'),
        name='zenoh_router',
        max_respawns=-1,
        respawn_delay=2.0,
    )
    description = read_robot_description(
        DESCRIPTION_PACKAGE,
        f'{ROBOT_NAME}.urdf.xacro',
        xacro_args=[
            f'gripper:={GRIPPER}',
            'sim_mujoco:=true',
            'use_fake_hardware:=true',
        ],
    )
    robot_state_publisher(
        description, node_name='robot_state_publisher', anonymous=False)
    bl.process(
        [os.path.join(install_directory, 'lib', 'mujoco_ros2_control',
                      'robot_description_to_mjcf.sh'),
         '--publish_topic', '/mujoco_robot_description',
         '--convert_stl_to_obj',
         '--mujoco_inputs',
         os.path.abspath('manipulation/config/mujoco_inputs.xml'),
         '--scene',
         write_rendered_scene_file()],
        name='mjcf_converter',
    )
    bl.node(
        'controller_manager', 'ros2_control_node',
        name='controller_manager',
        anonymous=False,
        param_files=[
            os.path.join(
                install_directory, 'share', CONTROL_PACKAGE, 'config',
                'kortex3_sim_controllers.yaml'),
            os.path.abspath('manipulation/config/mujoco_plugins.yaml'),
        ],
        use_sim_time=True,
    )
    spawn_controller('joint_state_broadcaster')
    spawn_controller('joint_trajectory_controller')
    spawn_controller('robotiq_gripper_controller')

    bl.process(
        'python manipulation/src/mujoco_planning_scene.py',
        name='mujoco_planning_scene',
    )
    bl.include(
        MOVEIT_PACKAGE, 'move_group.launch.py',
        pass_launch_func_args=False,
        use_sim_time='true',
        capabilities='move_group/ExecuteTaskSolutionCapability',
    )
    bl.include(
        'play_motion2', 'play_motion2.launch.py',
        pass_launch_func_args=False,
        motions_file=os.path.abspath('manipulation/config/motions.yaml'),
        motion_planner_config=os.path.abspath(
            'manipulation/config/motion_planner.yaml'),
        use_sim_time='true',
    )
    bl.process(
        'rviz2 -d ' + os.path.abspath('manipulation/config/moveit.rviz')
        + ' --ros-args -p use_sim_time:=true',
        name='rviz',
    )
