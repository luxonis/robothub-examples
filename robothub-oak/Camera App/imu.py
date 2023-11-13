from kalman import Kalman
import collections
import numpy as np
import math


class Context:
    Samples = 200
    accAngleX_kalman = Kalman()
    accAngleY_kalman = Kalman()
    AccErrorX = 0
    AccErrorY = 0
    accAngleX = 0
    accAngleY = 0

    GyroErrorX = 0
    GyroErrorY = 0
    GyroErrorZ = 0

    acc_offset = None
    gyro_offset = None

    def finish_IMU_offset(self):
        self.AccErrorX = self.AccErrorX / self.Samples
        self.AccErrorY = self.AccErrorY / self.Samples

        self.GyroErrorX = self.GyroErrorX / self.Samples
        self.GyroErrorY = self.GyroErrorY / self.Samples
        self.GyroErrorZ = self.GyroErrorZ / self.Samples

        self.accAngleX_kalman.setAngle(self.accAngleX - self.AccErrorX)
        self.accAngleY_kalman.setAngle(self.accAngleY - self.AccErrorY)

        self.acc_offset = (self.AccErrorX, self.AccErrorY)
        self.gyro_offset = (self.GyroErrorX, self.GyroErrorY, self.GyroErrorZ)

        self.baseTs = None
        self.current_time_acc = 0
        self.current_time_gyro = 0
        self.gyroAngleX = -self.gyro_offset[0]
        self.gyroAngleY = -self.gyro_offset[1]
        self.gyroAngleZ = -self.gyro_offset[2]
        self.yaw = 0

        self.learning_buffer = 10
        self.roll_buffer = collections.deque(maxlen=self.learning_buffer)
        self.pitch_buffer = collections.deque(maxlen=self.learning_buffer)
        self.yaw_buffer = collections.deque(maxlen=self.learning_buffer)

def calculate_IMU_offset_step(imuPackets, ctx: Context):
    for imuPacket in imuPackets:
        # Read Values
        acceleroValues = imuPacket.acceleroMeter
        gyroValues = imuPacket.gyroscope

        # Compute degree values
        ctx.accAngleX = math.atan2(acceleroValues.y, acceleroValues.z) * 180 / math.pi
        ctx.accAngleY = math.atan2(acceleroValues.z, acceleroValues.x) * 180 / math.pi

        # Acc increment in degrees
        ctx.AccErrorX += ctx.accAngleX
        ctx.AccErrorY += ctx.accAngleY

        GyroX = gyroValues.x * 180 / math.pi
        GyroY = gyroValues.y * 180 / math.pi
        GyroZ = gyroValues.z * 180 / math.pi

        # Gyro increment in degrees
        ctx.GyroErrorX += GyroX
        ctx.GyroErrorY += GyroY
        ctx.GyroErrorZ += GyroZ

def timeDeltaToMilliS(delta) -> float:
    return delta.total_seconds() * 1000

def process_packets(imuPackets, ctx: Context):
    for imuPacket in imuPackets:
        # Read Values
        acceleroValues = imuPacket.acceleroMeter
        gyroValues = imuPacket.gyroscope

        # Read timestamps
        acceleroTs = acceleroValues.getTimestampDevice()
        gyroTs = gyroValues.getTimestampDevice()

        if ctx.baseTs is None:
            ctx.baseTs = acceleroTs if acceleroTs < gyroTs else gyroTs

        # Compute degree values for acc - offset
        acceleroTs = timeDeltaToMilliS(acceleroTs - ctx.baseTs)
        accAngleX = math.atan2(acceleroValues.y, acceleroValues.z) * 180 / math.pi - ctx.acc_offset[0]
        accAngleY = math.atan2(acceleroValues.z, acceleroValues.x) * 180 / math.pi - ctx.acc_offset[1]
        elapsed_time_acc = acceleroTs - ctx.current_time_acc
        ctx.current_time_acc = acceleroTs

        # Rad/s -> degree/s conversion
        gyroTs = timeDeltaToMilliS(gyroTs - ctx.baseTs)
        GyroX = (gyroValues.x * 180 / math.pi)
        GyroY = (gyroValues.y * 180 / math.pi)
        GyroZ = (gyroValues.z * 180 / math.pi)

        elapsed_time_gyro = gyroTs - ctx.current_time_gyro
        ctx.current_time_gyro = gyroTs

        # Degree/s -> degree conversion for current time
        ctx.gyroAngleX += GyroX * (elapsed_time_gyro / 1000)
        ctx.gyroAngleY += GyroY * (elapsed_time_gyro / 1000)
        ctx.gyroAngleZ += GyroZ * (elapsed_time_gyro / 1000)

        # Gyro reset on +-360 degrees  (gyro overflow elimination)
        if GyroX == 360 or GyroX == -360:
            GyroX = 0

        # Acc/Gyro angle reset
        # X coordinate
        if -200 <= int(ctx.gyroAngleX - accAngleX) < -160:
            accAngleX = accAngleX - 180
        if 200 >= int(ctx.gyroAngleX - accAngleX) > 160:
            accAngleX = accAngleX + 180

        if int(ctx.gyroAngleX - accAngleX) < -300:
            accAngleX = accAngleX - 360
        if int(ctx.gyroAngleX - accAngleX) > 300:
            accAngleX = accAngleX + 360

        # Y coordinate
        if GyroY == 360 or GyroY == -360:
            GyroY = 0

        if -200 <= int(ctx.gyroAngleY - accAngleY) < -160:
            accAngleY = accAngleY - 180
        if 200 >= int(ctx.gyroAngleY - accAngleY) > 160:
            accAngleY = accAngleY + 180

        if int(ctx.gyroAngleY - accAngleY) < -300:
            accAngleY = accAngleY - 360
        if int(ctx.gyroAngleY - accAngleY) > 300:
            accAngleY = accAngleY + 360

        # Read value from calman filter
        accAngleX_k = ctx.accAngleX_kalman.getAngle(accAngleX, GyroX, elapsed_time_acc / 1000)[0]
        accAngleY_k = ctx.accAngleY_kalman.getAngle(accAngleY, GyroY, elapsed_time_acc / 1000)[0]

        # Use complementary filter
        # Use complementary filter if difference between Gyro and Acc angle < 10
        if abs(ctx.gyroAngleY - accAngleY_k) < 10:
            pitch = 0.9 * ctx.gyroAngleY + (0.1 * accAngleY_k)
        else:
            pitch = ctx.gyroAngleY

        if abs(ctx.gyroAngleX - accAngleX_k) < 10:
            roll = 0.9 * ctx.gyroAngleX + (0.1 * accAngleX_k)
        else:
            roll = ctx.gyroAngleX

        # Compute yaw in degrees
        ctx.yaw += GyroZ * (elapsed_time_acc / 1000)
        # print("GA-X: " + str(gyroAngleX) + " A-X: " + str(accAngleX_k))
        # print("GA-Y: " + str(gyroAngleY) + " A-Y: " + str(accAngleY_k))

        # Reset the gyro angle when it has drifted too much in X=0,Y=0 position
        if ((5 < abs(ctx.gyroAngleX - accAngleX_k)) or (5 < abs(ctx.gyroAngleY - accAngleY_k))) and 0 <= abs(int(accAngleX_k)) < 2 and 0 <= abs(int(accAngleY_k)) < 2:
            ctx.gyroAngleX = accAngleX_k.copy()
            ctx.gyroAngleY = accAngleY_k.copy()
            ctx.yaw = 0

        ctx.pitch_buffer.append(pitch)
        ctx.yaw_buffer.append(ctx.yaw)
        ctx.roll_buffer.append(roll)

        pitch = np.mean(ctx.pitch_buffer)
        ctx.yaw = np.mean(ctx.yaw)
        roll = np.mean(roll)

        return [math.radians(np.round(-pitch, 0)),
            math.radians(np.round(-ctx.yaw, 0)),
            math.radians(np.round(-roll, 0)),
        ]
        # Rotation transformation
        # if (85 <= abs(int(pitch)) < 180 or 265 <= abs(int(pitch)) < 360) and not 85 < abs(int(roll)) < 95:
        #     return [math.radians(np.round(-pitch, 0)),
        #         math.radians(np.round(-roll, 0)),
        #         math.radians(np.round(-ctx.yaw, 0))
        #     ]
        # else:
        #     return [math.radians(np.round(-pitch, 0)),
        #         math.radians(np.round(-ctx.yaw, 0)),
        #         math.radians(np.round(-roll, 0)),
        #     ]
        # return 
        # print("Pitch: " + str(-pitch))
        # print("Yaw: " + str(-ctx.yaw))
        # print("Roll: " + str(-roll))

        # # Rotation transformation
        # if (85 <= abs(int(pitch)) < 180 or 265 <= abs(int(pitch)) < 360) and not 85 < abs(int(roll)) < 95:
        #     camera.rotate([1, 0, 0], math.radians(np.round(-pitch, 0)))
        #     camera.rotate([0, 1, 0], math.radians(np.round(-roll, 0)))
        #     camera.rotate([0, 0, 1], math.radians(np.round(-ctx.yaw, 0)))
        # else:
        #     camera.rotate([1, 0, 0], math.radians(np.round(-pitch, 0)))
        #     camera.rotate([0, 1, 0], math.radians(np.round(-ctx.yaw, 0)))
        #     camera.rotate([0, 0, 1], math.radians(np.round(-roll, 0)))

        # mp.vectors = camera.vectors