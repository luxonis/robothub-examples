import contextlib
import logging as log
import os
import time

import depthai as dai
import robothub_core


class Application(robothub_core.RobotHubApplication):
    bootloader = None

    def on_start(self):
        log.info('Starting App')

    def start_execution(self):
        log.info(f'Connecting to assigned devices...')

        for device in robothub_core.DEVICES:
            print("=" * 20)
            mxid = device.oak["serialNumber"]
            name = device.oak["productName"]
            self.update_bl(mxid, name)

        log.info('App has successfully finished execution, you may uninstall it.')

    def progress_cb(self, value):
        print(f'Update progress: {100 * value:.2f}%')

    def update_bl(self, mxid, name):
        # Connect to device, check if its PoE and flash updated bootloader if so

        start_time = time.time()
        give_up_time = start_time + 20

        connected = False
        self.bootloader = None

        device_info = dai.DeviceInfo(mxid)
        while time.time() < give_up_time and self.running:
            try:
                with open(os.devnull, 'w') as devnull:
                    with contextlib.redirect_stdout(devnull):
                        self.bootloader = dai.DeviceBootloader(device_info, False)
                connected = True
                break
            except BaseException as e:
                # Device could not be connected to, wait 0.1 seconds and try again. 
                log.info(f"Could not connect to device {name} with error \'{e}\', retrying...")
                self.wait(0.1)
                continue
        # check if the device was connected and whether its PoE
        if self.running:
            if connected:
                log.info(f'Connected device with productName "{name}".')
                bootloader_type = self.bootloader.getType()
                self.bootloader.close()
                time.sleep(0.1)

                if bootloader_type == dai.DeviceBootloader.Type.NETWORK:
                    poe = True
                elif bootloader_type == dai.DeviceBootloader.Type.USB:
                    poe = False
                else:
                    log.error(f'Device bootloader is type {bootloader_type} which is not type "NETWORK" or "USB". '
                              f'If device is PoE-type and you can\'t update the bootloader, '
                              f'please contact customer support')
                    poe = False

                if poe:
                    log.info(f'Device is PoE-type, installing latest bootloader version. '
                             f'Don\'t disconnect device or stop the App!')
                    start_time = time.time()
                    give_up_time = start_time + 20
                    while time.time() < give_up_time and self.running:
                        try:
                            with open(os.devnull, 'w') as devnull:
                                with contextlib.redirect_stdout(devnull):
                                    self.bootloader = dai.DeviceBootloader(device_info, True)
                            connected = True
                            break
                        except BaseException as e:
                            # Device could not be connected to, wait 0.1 seconds and try again. 
                            # log.info(f"Could not connect to device {name} with error \'{e}\', retrying...")
                            self.wait(0.1)
                            continue
                    self.bootloader.flashBootloader(memory=dai.DeviceBootloader.Memory.FLASH,
                                                    type=dai.DeviceBootloader.Type.NETWORK,
                                                    progressCallback=self.progress_cb)
                    log.info(f'Successfully installed latest firmware on the device!')
                    self.bootloader.close()
                else:
                    log.info(f'Device is NOT PoE-type, skipping...')
            else:
                log.info(f'Device "{name}" could not be connected within 20s timeout. '
                         f'Please ensure device is connected correctly and try again.')

    def on_stop(self):
        log.info('Stopping App')
        if self.bootloader:
            try:
                with open(os.devnull, 'w') as devnull:
                    with contextlib.redirect_stdout(devnull):
                        self.bootloader.close()
            except BaseException as e:
                log.debug(f'Could not close device with error: {e}')
        log.info('App Stopped')
