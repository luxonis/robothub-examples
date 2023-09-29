# RGB Stream

This App uploads a DepthAI pipeline to each assigned device and streams RGB sensor output.

You can easily replace the RGB streaming pipeline in the template with a pipeline of your own. To do this, edit
the `build_pipeline()` and `process_output()` functions accordingly.

## Requirements

- Luxonis device with an RGB sensor.

## Usage

- Assign devices to the App and launch it, one color stream will be started for each device. You can use the
  Configuration tab to change FPS of the streams. 
