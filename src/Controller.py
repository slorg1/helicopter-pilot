import attr
from attr import validators
from threading import Thread, Condition
import serial
import os
import time
import logging


@attr.s(slots=True,)
class Controller(object):
    """
        Controls a S107G programmatically over an arduino.

        Set the desired states on an instance of this class and L{send<Controller.send>} them over to the
        helicopter.
    """

    DEF_PITCH = 63
    """ Default pitch setting """

    DEF_YAW = 63
    """ Default yaw setting"""

    DEF_TRIM = 63
    """ Default trim setting """

    DEF_THROTTLE = 0
    """ Default throttle setting"""

    MAX_PITCH = 126
    """ Maximum pitch setting """

    MAX_YAW = 126
    """ Maximum yaw setting """

    MAX_TRIM = 126
    """ Maximum trim setting """

    MAX_THROTTLE = 127
    """ Maximum throttle setting """

    pitch = attr.ib(validator=validators.in_(frozenset(range(0, MAX_PITCH,))), default=DEF_PITCH,)
    """
        The pitch for this entity, nose up and down.

        Values below L{Helicopter.DEF_PITCH} bring the nose down: forward
        Values above L{Helicopter.DEF_PITCH} bring the nose up: backward
    """

    yaw = attr.ib(validator=validators.in_(frozenset(range(0, MAX_YAW,))), default=DEF_YAW,)
    """
        The yaw, left/right.

        Values below L{Controller.DEF_YAW} turn the nose counter clock wise (to the right)
        Values below L{Controller.DEF_YAW} turn the nose clock clock wise (to the left)
    """

    trim = attr.ib(validator=validators.in_(frozenset(range(0, MAX_TRIM,))), default=DEF_TRIM,)
    """
        The trim, left/right.

        Values above L{Controller.DEF_TRIM} to the right
        Values below L{Controller.DEF_TRIM} to the left
    """

    throttle = attr.ib(validator=validators.in_(frozenset(range(0, MAX_THROTTLE,))), default=DEF_THROTTLE,)
    """ The throttle for this entity (gas!) """

    def __attrs_post_init__(self):
        self.reset()

        root_dir = '/dev'

        path = next(
                    (
                        x
                        for x in os.listdir(root_dir)
                        if x.startswith('ttyACM')
                    ),
                    None,
                    )

        if not path:
            raise ConnectionError("Could find and connect to the helicopter controller")

        path = os.path.join(root_dir, path)

        self.__serial_connection = serial.Serial(path, 9600)
        self.__serial_connection.flushInput()  # cleans up anything lingering

        ser = self.__serial_connection
        my_heli = self

        def f():
            while my_heli.__connection_up is False:
                try:
                    ser_bytes = ser.readline()
                    read_str = ser_bytes.decode('utf-8').strip()

                    Controller.__LOGGER.debug("ACK: %s", read_str,)

                    if read_str == "READY":
                        with my_heli.__available:
                            my_heli.__connection_up = True
                            my_heli.__available.notify()
                except:
                    Controller.__LOGGER.warn("Error while working with the serial connection", exc_info=1)

                    with self.__available:
                        my_heli.__connection_up = None
                        my_heli.__available.notify()

        t = Thread(target=f, daemon=True,)
        t.start()

    def reset(self,):
        """
            Configures the desired state of the helicopter to neutral and no gaz.
        """
        (
            self.yaw, self.pitch, self.throttle, self.trim
        ) = (
                Controller.DEF_YAW, Controller.DEF_PITCH, Controller.DEF_THROTTLE, Controller.DEF_TRIM,
            )

    def is_ready(self):
        """
            Returns C{True} if this helicopter is ready for flight.

            @rtype: bool
        """
        with self.__available:
            if self.__connection_up is False:
                self.__available.wait()

                if self.__connection_up is True:
                    Controller.__LOGGER.info("Ready to go!")

        if self.__connection_up is None:
            Controller.__LOGGER.error("Connection failed.")
            return False

        assert self.__connection_up is True

        return True

    def send(self):
        """
            Sends the configured desired state of the helicopter to the remote controller.

            Waits for the helicopter to be ready for flight L{automatically<Heli.is_ready>}.
        """
        if not self.is_ready():
            Controller.__LOGGER.error("Cannot send desired state: no connection available.")
            return

        msg = [self.yaw, self.pitch, self.throttle, self.trim]
        written_bytes = self.__serial_connection.write(msg)

        assert written_bytes == len(msg)

        self.__serial_connection.flush()

        Controller.__LOGGER.debug("Sent %d %d %d %d", *msg)

        # this is to wait for the arduino to get it, we could implement an ACK
        time.sleep(0.2)

    def land(self):
        """
            Resets the state of the helicopter to the L{initial<Heli.initial>} state (i.e. crash lands).
        """
        self.reset()
        self.send()

    __serial_connection = attr.ib(validator=validators.instance_of((serial.Serial, type(None),)), default=None)

    __connection_up = attr.ib(validator=validators.instance_of(bool), default=False,)

    __available = attr.ib(validator=validators.instance_of(Condition,), factory=Condition,)

    __LOGGER = logging.getLogger(__name__)
