# Robothub Examples

This repository contains examples of [RobotHub Perception Apps](https://hub-docs.luxonis.com/docs/perception-apps/overview). Examples must be run through RobotHub, they do not serve as stand-alone code and cannot be simply executed locally. 

Based on abstraction level, Apps can be divided into three categories:
1. Robothub-depthai Apps - Apps based on the [robothub-depthai](https://github.com/luxonis/robothub-depthai) library which abstracts away both communication with the RobotHub Cloud and construction of DepthAI pipelines. Strongly recommended for beginners in the RobotHub/DepthAI ecosystem, ideal for most use-cases.
2. Apps based on [Depthai_SDK](https://docs.luxonis.com/projects/sdk/en/latest/index.html). These Apps use Depthai_SDK to abstract away construction of the DepthAI pipeline but handle communication with the Cloud manually - through the [RobotHub SDK API](https://hub-docs.luxonis.com/docs/perception-apps/sdk-reference). Generally lower-level and with more boiler-plate than option 1, but allows for more customization. 
3. Apps based on [DepthAI](https://docs.luxonis.com/en/latest/). This way of development might be preferable for advanced users who are already familiar with DepthAI. Communication with devices is handled in DepthAI, communication with the cloud through the [RobotHub SDK API](https://hub-docs.luxonis.com/docs/perception-apps/sdk-reference).

