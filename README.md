# VR Stick Mapper
_A functional translation layer between SteamVR devices and VJoy virtual joysticks_

Inspired by the [steam-vr-wheel](https://github.com/mdovgialo/steam-vr-wheel) library.

## Dependencies

This tool is a translation layer between [SteamVR](https://www.steamvr.com/en/) and [VJoy](https://vjoy.en.softonic.com/), and thus relies on both being installed on your computer. It is, thus far, tested only on Windows machines running Windows Mixed Reality, but is likely to work on Windows machines running any SteamVR-compatible virtual reality interface.

## How to use

If you want to use one of the prebuilt controller mappings, you can run it via the `map` script in the `bin` directory, like so: `./bin/map <mapping name>`, e.g. `./bin/map wheel`

Feel free to add your own mappings to the script and run them that way.

## Features

### Mappings

Controller mappings require some list of devices, by device class and role, and define functions to translate those devices' inputs into VJoy axes and buttons, as well as a set of event triggers to provide contextual haptic feedback.


### Nodes

Nodes take some piece(s) of state and perform a simple operation on it, usually converting it to either a float value or a button value.

### Axes

Axes produce a floating point value. Since VJoy axes expect a value between 0 and 1 (well, 0 and 32767, but we handle that bit behind the scenes), there are several helpers to scale, clamp, and otherwise manipulate your axis values to be compatible with VJoy axes.

### Buttons

Buttons produce both a boolean state value and a four-state pairing of their current state and the previous tick's state, to allow effects when a button is first pressed or first released.

### Composites

You can translate and combine buttons and axes easily - an `AxisThresholdButton` is active when an axis value exceeds a specified threshold, you can combine buttons with arbitrary logic gates, reset an axis to a defined zero value when a button is pressed, etc. Combining the simple building blocks provided, you can produce highly refined input values, such as:

* An axis whose value can be adjusted when a button is pressed, but remains fixed at its current value when the button is released (a `PushPullAxis`)
* Arbitrarily complex gestures representing a sequence of movements along any number of axes
* Actions restricted to a particular position, either in absolute space or relative to the user's HMD
* Switching an axis between any number of complex inputs based on a series of gestures being performed
* And infinitely more

## Implementation

### Graph-based functional model

Each node has a single output and an arbitrary list of dependencies, and dependencies can nest to arbitrary depths. All state flows from the root `VrSystemState` node, with each node performing a simple operation on its inputs to produce an output.

### No repeated computation

Nodes implement the multiton pattern, meaning that initializing a node with the same parameters and inputs twice produces the same in-memory object. This allows your mapping to reuse the same nodes across multiple sections without needing to implement caching yourself - the node will only compute once once all of its dependencies have been computed for the current tick.

### Simple math

Once a graph is initialized, the only operations taking place are simple floating point math and boolean logic. One tick through a graph of any complexity is blazing fast.
