import numpy as np

class Kalman(object):

    def __init__(self, Q_angle=0.001, Q_bias=0.003, R_measure=0.03):
        self.Q_angle = Q_angle
        self.Q_bias = Q_bias
        self.R_measure = R_measure

        self.angle = 0
        self.bias = 0

        self.P = np.zeros((2, 2))
        self.K = np.zeros((2, 1))
        self.P[0][0] = 0
        self.P[0][1] = 0
        self.P[1][0] = 0
        self.P[1][1] = 0

    def getAngle(self, newAngle, newRate, dt):
        """
        :param newAngle: Angle from ACC in degrees
        :param newRate: Angle from Gyro in degrees/s
        :param dt: delta time in seconds
        """

        # Discrete Kalman filter time update equations - Time Update ("Predict")
        self.rate = newRate - self.bias
        self.angle += dt * self.rate

        # Update estimation error covariance - Project the error covariance ahead
        self.P[0][0] += dt * (dt * self.P[1][1] - self.P[0][1] - self.P[1][0] + self.Q_angle)
        self.P[0][1] -= dt * self.P[1][1]
        self.P[1][0] -= dt * self.P[1][1]
        self.P[1][1] += self.Q_bias * dt

        # Discrete Kalman filter measurement update equations - Measurement Update ("Correct")
        # Calculate Kalman gain - Compute the Kalman gain
        S = self.P[0][0] + self.R_measure
        self.K[0] = self.P[0][0] / S
        self.K[1] = self.P[1][0] / S

        # Calculate angle and bias - Update estimate with measurement zk (newAngle)
        y = newAngle - self.angle
        self.angle += self.K[0] * y
        self.bias += self.K[1] * y

        # Calculate estimation error covariance - Update the error covariance
        self.P[0][0] -= self.K[0] * self.P[0][0]
        self.P[0][1] -= self.K[0] * self.P[0][1]
        self.P[1][0] -= self.K[1] * self.P[0][0]
        self.P[1][1] -= self.K[1] * self.P[0][1]

        return self.angle

    def setAngle(self, newAngle):
        self.angle = newAngle

    def getRate(self):
        return self.rate