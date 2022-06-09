# Design decisions
## usage scope of config file
Using the config constants everywhere directly and never passing it to an constructor etc has the onyl downside that the components are less flexible in the context that they must be used with a condif file.
HOwever using the config glaobally makes it more consistent and often also better readable.
Using the settings everywhere also ensures that they are not bypassed accidentally.
Therfore the config constants are used as direct as possible.
This means that also parameters with default value for functions are likely to be removed in favor of directly using the constant in the function.