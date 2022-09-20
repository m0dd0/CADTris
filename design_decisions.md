# Design decisions
## Usage scope of config file
Using the config constants everywhere directly and never passing it to an constructor etc has the onyl downside that the components are less flexible in the context that they must be used with a condif file.
HOwever using the config glaobally makes it more consistent and often also better readable.
Using the settings everywhere also ensures that they are not bypassed accidentally.
Therfore the config constants are used as direct as possible.
This means that also parameters with default value for functions are likely to be removed in favor of directly using the constant in the function.

## Dynamic architecture setup
The game instance is only responsible for the game logic itself. It is not connect to the FusionAPI.
The game instance receives a display instance which is responsible for visualizing the current state of the game.
This allows us to have multiple displays to e.g. test the game logic with a dummy console display.
Everytime something changes in the game the game instance calls the update method of its display.
Therfore each display must has implemented an update method.
Changes in the game can occur due to different reasons. E.g user input or inout from a periodic deamon etc.
However the game itself cannot detect from where it got changed and therefore also the display doesnt have this information.
This makes sense as the only responsibility of the display is to visualize the current state of the game.
When using Fusion one Problem arises from this: Depending on whether the display update mechanism is called from a thread or from an event handler the actions which manipulate Fusion must be executed differently.
To achieve this the Fusion display instance receives a executer which tracks whether currently there is an event handler active or not and executes the demanded manipulating tasks from the display either by simply executing them or by using the event-doExecute mechanism.