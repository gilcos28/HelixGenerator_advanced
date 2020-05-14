#Author-Gil Cohen
#Description-Based on the Helix Generator plug-in and will allow the user to spiral helix with changing radius and height pitch from point-to-point.
# Importing sample Fusion Command
# Could import multiple Command definitions here

from .Helix_Advanced_Command import Helix_Advanced_Command

commands = []
command_definitions = []

# Define parameters for vent maker command
cmd = {
    'cmd_name': 'Helix Plus',
    'cmd_description': 'Create an Approximate variable Helical Curve',
    'cmd_resources': './resources',
    'cmd_id': 'cmdID_Helix_Advanced_Command',
    'workspace': 'FusionSolidEnvironment',
    'toolbar_panel_id': 'SketchPanel',
    'class': Helix_Advanced_Command
}
command_definitions.append(cmd)

# Set to True to display various useful messages when debugging your app
debug = False

# Don't change anything below here:
for cmd_def in command_definitions:
    command = cmd_def['class'](cmd_def, debug)
    commands.append(command)


def run(context):
    for run_command in commands:
        run_command.on_run()


def stop(context):
    for stop_command in commands:
        stop_command.on_stop()
