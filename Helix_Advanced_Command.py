import traceback
import adsk.core
import adsk.fusion
import math
from .Fusion360Utilities.Fusion360CommandBase import Fusion360CommandBase
from .Fusion360Utilities.Fusion360Utilities import get_app_objects
import sys
sys.path.append("C:\Z-Other\Python37\Lib\site-packages")
import numpy as np
from Equation import Expression

# You could change back to this function to create the variable helix
# you will want to do something about adjusting for the resolution in the t multiplier
# As it is now the higher the resolution the wider the curve will get.
# need to do something like t/resolution probably
def variable_helix_point(radius, pitch, resolution, t):
    # Helix math
    x = (.25*t+.5)*radius * math.cos(2*math.pi*t/resolution)
    y = (.25*t+.5)*radius * math.sin(2*math.pi*t/resolution)
    z = pitch * t / resolution

    # Create Fusion point
    point = adsk.core.Point3D.create(x, y, z)
    return point


# Generic Math Function to generate a point on a helix
def helix_point(radius, pitch, resolution, t, fnR, DT1, SP1, accumulator, fnZ, DT2, SP2, Z_previous, message_string):

    skip_ = False
    # Helix math
    # radius = radius * math.pow(r1 * 1.0,t)  #Gil
    DT_temp = SP1 + (t*DT1)
    try:
        radius = fnR(DT_temp, radius, resolution)
    except ZeroDivisionError:
        message_string = message_string + "<br>WARNING: Zero division for radius at [t]=" + str(t*DT1) + "<br>   -> skip point calculation"
        skip_ = True
        radius = 0   # nonsignificant value to return
    # if radius == None:
        # radius = 1      # when there's no equation in the equation tab then give it a value of 1 for user visualization
    x = radius * math.cos(2*math.pi*t/resolution)
    y = radius * math.sin(2*math.pi*t/resolution)
    # z = pitch * t / resolution

    DT_temp = SP2 + (t*DT2)
    if accumulator:
        z = Z_previous[0] + Z_previous[1]
        Z_previous[0] = z
        if t == 0:
            Z_previous[1] = pitch
        else:
            Z_previous[1] = Z_previous[1] * fnZ(DT_temp, pitch, resolution)  #z1
    else:
        # z = t * pitch / resolution
        try:
            z = fnZ(DT_temp,pitch, resolution)
        except ZeroDivisionError:
            message_string = message_string + "<br>WARNING: Zero division for pitch at [t]=" + str(t*DT2) + "<br>   -> skip point calculation"
            skip_ = True
            z = 0   # nonsignificant value to return
        # if z == None:    # when there's no equation in the equation tab then give it a value of 1 for user visualization
            # z = 1

    # Create Fusion point
    point = adsk.core.Point3D.create(x, y, z)
    return point, Z_previous, skip_, message_string


# Generates a Helix in Fusionthem
def helix_maker(radius, revolutions, pitch, resolution, r1, DT1, SP1, accumulator, z1, DT2, SP2, plane, points_old):

    # Gil
    Z_previous = np.zeros(2) # 0-the previous Z value, 1-the accumulator
    message_string = ""

    # Gets necessary application objects
    app_objects = get_app_objects()

    # Get the root component of the active design.
    root_comp = app_objects['design'].rootComponent

    # Get Sketches Collection for Root component
    sketches = root_comp.sketches

    # Add sketch to selected plane
    sketch = sketches.add(plane)

    # Collection to hold helix points
    points = adsk.core.ObjectCollection.create()

    # app = adsk.core.Application.get()
    # ui  = app.userInterface
    # ui.messageBox(z1)

    # prepare equation
    # r1_input is thhie object itself, review get_inputs(command_inputs) at parent class Fusion360CommandBase
    # good start for classes documentation: http://help.autodesk.com/view/fusion360/ENU/?guid=GUID-8B9041D5-75CC-4515-B4BB-4CF2CD5BC359
    preview = True
    # fn = None
    try:
        fn = Expression(SP1, ["p", "r", "s", "n"])
        SP1 = fn(pitch, radius, resolution, revolutions)
    except:
        SP1 = None
    if SP1 is None:
        preview = False
        message_string = message_string + "<br>ERROR: radius starting point is incorrect"
    # fn = None
    try:
        fn = Expression(SP2, ["p", "r", "s", "n"])
        SP2 = fn(pitch, radius, resolution, revolutions)
    except:
        SP2 = None
    if SP2 is None:
        preview = False
        message_string = message_string + "<br>ERROR: pitch starting point is incorrect"
    try:
        fnR = Expression(r1,["t", "r", "s"])
        fn = fnR(3, pitch, resolution)  # test if equation is legal, if not use previous points (points_old)
    except:
        fn = None
    if fn is None:
        preview = False
        message_string = message_string + "<br>ERROR: radius equation not legal"
    try:
        fnZ = Expression(z1,["t", "p", "s"])
        fn = fnZ(3, pitch, resolution)
    except:
        fn = None
    if fn is None:
        preview = False
        message_string = message_string + "<br>ERROR: pitch equation not legal"
    if revolutions <= 0:
        preview = False
        message_string = message_string + "<br>ERROR: revolutions cannot be less than 0"

    if preview:
        # Iterate based on revolutions and resolution
        for t in range(0, int(revolutions*resolution)+1):
            # Add Point to collection
            point, Z_previous, skip_, message_string = helix_point(radius, pitch, resolution, t, fnR, DT1, SP1, accumulator, fnZ, DT2, SP2, Z_previous, message_string)
            if not skip_:
                points.add(point)

            # use this instead to create the variable helix
            # points.add(variable_helix_point(radius, pitch, resolution, t))

        # Create Spline through points
        sketch.sketchCurves.sketchFittedSplines.add(points)
        return points, message_string
    else:
        sketch.sketchCurves.sketchFittedSplines.add(points_old)
        return points_old, message_string

# THis is the class that contains the information about your command.
class Helix_Advanced_Command(Fusion360CommandBase):

    # Runs when Fusion command would generate a preview after all inputs are valid or changed
    def on_preview(self, command, inputs, args, input_values):

        # create a helix based on user inputs
        self.points_old, message_string = helix_maker(input_values['radius'],
                    input_values['revolutions'],
                    input_values['pitch'],
                    input_values['resolution'],
                    input_values['r1'],
                    input_values['DT1'],
                    input_values['SP1'],
                    input_values['accumulator'],
                    input_values['z1'],
                    input_values['DT2'],
                    input_values['SP2'],
                    input_values['plane'][0],
                    self.points_old)

        input_values['output_input'].formattedText = self.output_text + message_string

    # Runs when the user presses ok button
    def on_execute(self, command, inputs, args, input_values):

        # create a helix based on user inputs
        self.points_old = helix_maker(input_values['radius'],
                    input_values['revolutions'],
                    input_values['pitch'],
                    input_values['resolution'],
                    input_values['r1'],
                    input_values['DT1'],
                    input_values['SP1'],
                    input_values['accumulator'],
                    input_values['z1'],
                    input_values['DT2'],
                    input_values['SP2'],
                    input_values['plane'][0],
                    self.points_old)

    # Runs when user selects your command from Fusion UI, Build UI here
    def on_create(self, command, inputs):

        # Gets necessary application objects
        app_objects = get_app_objects()

        # Get users current units
        default_units = app_objects['units_manager'].defaultLengthUnits

        # initialize points_old with a default value
        self.points_old = adsk.core.ObjectCollection.create()
        self.points_old.add(adsk.core.Point3D.create(0, 0, 0))
        self.points_old.add(adsk.core.Point3D.create(1, 1, 1))

        # Create a tabs input.
        tabCmd1 = inputs.addTabCommandInput('tab_1', 'Inputs')
        tabInputs1 = tabCmd1.children
        tabCmd2 = inputs.addTabCommandInput('tab_2', 'Read me')
        tabInputs2 = tabCmd2.children

        # Create the Selection input to have a planar face or construction plane selected.
        selection_input = tabInputs1.addSelectionInput('plane', 'Plane', 'Select sketch plane.')
        selection_input.addSelectionFilter('PlanarFaces')
        selection_input.addSelectionFilter('ConstructionPlanes')
        selection_input.setSelectionLimits(1, 1)

        # Radius of the helix
        radius_input = adsk.core.ValueInput.createByReal(2.554)
        tabInputs1.addValueInput('radius', 'Radius', default_units, radius_input)

        # Pitch of the helix
        pitch_input = adsk.core.ValueInput.createByReal(2.554)
        tabInputs1.addValueInput('pitch', 'Pitch', default_units, pitch_input)

        # Define points per revolution -> resolution
        tabInputs1.addIntegerSpinnerCommandInput('resolution', 'Resolution', 0, 1000, 1, 10)

        # Number of revolutions
        tabInputs1.addIntegerSpinnerCommandInput('revolutions', 'Revolutions', 0, 1000, 1, 5)

        # input radius Equation
        tabInputs1.addStringValueInput ('r1', 'Radius Eq (t,r,s)', 'r') # r*(0.95^t)

        # Radius steps of Incrimination
        DT1_input = adsk.core.ValueInput.createByReal(1)
        tabInputs1.addValueInput('DT1', 'Delta Tr', '', DT1_input)

        # start counting from
        # start_r_input = adsk.core.ValueInput.createByReal(0)
        # tabInputs1.addValueInput('SP1', 'start counting at', '', start_r_input)
        tabInputs1.addStringValueInput('SP1', 'start counting at', '0')

        # accumulator algorithm for Z axis
        accumulator = tabInputs1.addBoolValueInput('accumulator', 'Accumulator on', True, '', False)

        # input height Equation
        tabInputs1.addStringValueInput('z1', 'Pitch Eq (t,p,s)', 't*p/s')

        # height steps of Incrimination
        DT2_input = adsk.core.ValueInput.createByReal(1)
        tabInputs1.addValueInput('DT2', 'Delta Tp', '', DT2_input)

        # start counting from
        # start_p_input = adsk.core.ValueInput.createByReal(0)
        # tabInputs1.addValueInput('SP2', 'start counting at', '', start_p_input)
        tabInputs1.addStringValueInput('SP2', 'start counting at', '0')

        # output window
        self.output_text = "Message Output:"
        tabInputs1.addTextBoxCommandInput ('output', '', self.output_text, 5, True)

        # instruction <em> <u> <p>
        Instruction = "<b><u>Instruction</u><br>"\
            + "<em><u>Variable’s:</u></em><br>"\
            + "r -</b> radius, <b>p -</b> pitch,<br> <b>s -</b> resolution, <b>n -</b> revolutions<br>"\
            + "<b>t</b> - counter variable, (default value 0)<br>"\
            + "<b><em><u>Equation Input:</u></em></b><br>"\
            + "Utilize python “Equation Interpreter”<br>"\
            + "It can be: const,cos(x),sin(x),t^x,pi,e …<br>"\
            + "<b><em><u>Calculation methods:</u></em></b><br>"\
            + "<b>Radius:</b> the equation calculates the radius size. Then internally it’s converted to X, Y points with the following equations<br>"\
            + "x = radius *cos(2*pi*t/resolution)<br>"\
            + "y = radius *sin(2*pi*t/resolution)<br>"\
            + "<b>Pitch:</b> the equation is calculated directly. The result translates directly to Z axis.<br>"\
            + "<b>[t] -</b> variable that count from 0 (by default) to Resolution*Revolutions+1.<br>"\
            + "<b>[Tr] -</b> steps for <b>[t]</b> radius <br>"\
            + "<b>[Tp] -</b> steps for <b>[t]</b> pitch <br>"\
            + "<b>start counting at –</b> configure <b>[t]</b> counter starting point (Accept variable’s [r,p,s,n])<br>"\
            + "<b><em><u>Accumulator (pitch only):</u></em></b><br>"\
            + "<em>[sum of previous results] +<br>"\
            + "([current result] * [pitch Eq])</em><br>"\
            + "Where [current results] initial value is pitch<br>"\
            + "<b><em><u>Message Output:</u></em></b><br>"\
            + "Output WARNING/ERROR messages"

        tabInputs2.addTextBoxCommandInput ('instruction', '', Instruction, 32, True)

        # radioButtonGroup = inputs.addRadioButtonGroupCommandInput('radioImportExport', ' Import or Export ')
        # radioButtonGroup.isFullWidth = True
        # radioButtonItems = radioButtonGroup.listItems
        # radioButtonItems.add('Import', True)
        # radioButtonItems.add('Export', False)

        # sliderInput = inputs.addIntegerSliderCommandInput('sliderCommandInput', 'Slider', 0, 10, False)
