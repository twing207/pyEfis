#!/usr/bin/env python

#  Copyright (c) 2013 Phil Birkelbach
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import sys, Queue
import argparse
import ConfigParser  # configparser for Python 3
from PyQt4.QtGui import *
from PyQt4.QtCore import *

import fix
import gauges
import ai
import hsi
import airspeed
import altimeter
import fgfs

# This is a container object to hold the callback for the FIX thread
# which when called emits the signals for each parameter


class FlightData (QObject):
    rollChanged = pyqtSignal(float, name="rollChanged")
    pitchChanged = pyqtSignal(float, name="pitchChanged")
    headingChanged = pyqtSignal(float, name="headingChanged")

    def getParameter(self, param):
        if param.name == "Roll Angle":
            self.rollChanged.emit(param.value)
        elif param.name == "Pitch Angle":
            self.pitchChanged.emit(param.value)
        elif param.name == "Heading":
            self.headingChanged.emit(param.value)


class main (QMainWindow):
    def __init__(self, test, parent=None):
        super(main, self).__init__(parent)

        config = ConfigParser.RawConfigParser()
        config.read('config')
        self.width = int(config.get("Screen", "screenSize.Width"))
        self.height = int(config.get("Screen", "screenSize.Height"))
        self.screenColor = config.get("Screen", "screenColor")
        self.canAdapter = config.get("CAN-FIX", "canAdapter")
        self.canDevice = config.get("CAN-FIX", "canDevice")
        self.queue = Queue.Queue()
        self.setupUi(self, test)

        if test == 'normal':
            self.flightData = FlightData()
            self.cfix = fix.Fix(self.canAdapter, self.canDevice)
            self.cfix.setParameterCallback(self.flightData.getParameter)

    def setupUi(self, MainWindow, test):
        MainWindow.setObjectName("PFD")
        MainWindow.resize(self.width, self.height)
        w = QWidget(MainWindow)
        w.setGeometry(0, 0, self.width, self.height)

        p = w.palette()
        if self.screenColor:
            p.setColor(w.backgroundRole(), QColor(self.screenColor))
            w.setPalette(p)
            w.setAutoFillBackground(True)
        instWidth = self.width - 410
        instHeight = self.height - 200
        self.a = ai.AI(w)
        self.a.resize(instWidth, instHeight)
        self.a.move(100, 100)

        self.alt_tape = altimeter.Altimeter_Tape(w)
        self.alt_tape.resize(100, instHeight)
        self.alt_tape.move(instWidth + 100, 100)

        self.as_tape = airspeed.Airspeed_Tape(w)
        self.as_tape.resize(100, instHeight)
        self.as_tape.move(0, 100)

        self.head_tape = hsi.DG_Tape(w)
        self.head_tape.resize(instWidth, 100)
        self.head_tape.move(100, instHeight + 100)

        map = gauges.RoundGauge(w)
        map.name = "MAP"
        map.decimalPlaces = 1
        map.lowRange = 0.0
        map.highRange = 30.0
        map.highWarn = 28.0
        map.highAlarm = 29.0
        map.resize(200, 100)
        map.move(w.width() - 200, 100)

        self.rpm = gauges.RoundGauge(w)
        self.rpm.name = "RPM"
        self.rpm.decimalPlaces = 0
        self.rpm.lowRange = 0.0
        self.rpm.highRange = 2800.0
        self.rpm.highWarn = 2600.0
        self.rpm.highAlarm = 2760.0
        self.rpm.resize(200, 100)
        self.rpm.move(w.width() - 200, 0)

        self.op = gauges.HorizontalBar(w)
        self.op.name = "Oil Press"
        self.op.units = "psi"
        self.op.decimalPlaces = 1
        self.op.lowRange = 0.0
        self.op.highRange = 100.0
        self.op.highWarn = 90.0
        self.op.highAlarm = 95.0
        self.op.lowWarn = 45.0
        self.op.lowAlarm = 10.0
        self.op.resize(190, 75)
        self.op.move(w.width() - 200, 220)
        self.op.value = 45.2

        self.ot = gauges.HorizontalBar(w)
        self.ot.name = "Oil Temp"
        self.ot.units = "degF"
        self.ot.decimalPlaces = 1
        self.ot.lowRange = 160.0
        self.ot.highRange = 250.0
        self.ot.highWarn = 210.0
        self.ot.highAlarm = 230.0
        self.ot.lowWarn = None
        self.ot.lowAlarm = None
        self.ot.resize(190, 75)
        self.ot.move(w.width() - 200, 300)
        self.ot.value = 215.2

        self.fuel = gauges.HorizontalBar(w)
        self.fuel.name = "Fuel Qty"
        self.fuel.units = "gal"
        self.fuel.decimalPlaces = 1
        self.fuel.lowRange = 0.0
        self.fuel.highRange = 50.0
        self.fuel.lowWarn = 2.0
        self.fuel.resize(190, 75)
        self.fuel.move(w.width() - 200, 380)
        self.fuel.value = 15.2

        self.ff = gauges.HorizontalBar(w)
        self.ff.name = "Fuel Flow"
        self.ff.units = "gph"
        self.ff.decimalPlaces = 1
        self.ff.lowRange = 0.0
        self.ff.highRange = 20.0
        self.ff.highWarn = None
        self.ff.highAlarm = None
        self.ff.lowWarn = None
        self.ff.lowAlarm = None
        self.ff.resize(190, 75)
        self.ff.move(w.width() - 200, 460)
        self.ff.value = 5.2

        cht = gauges.HorizontalBar(w)
        cht.name = "Max CHT"
        cht.units = "degF"
        cht.decimalPlaces = 0
        cht.lowRange = 0.0
        cht.highRange = 500.0
        cht.highWarn = 380
        cht.highAlarm = 400
        cht.resize(190, 75)
        cht.move(w.width() - 200, 540)
        cht.value = 350

        self.egt = gauges.HorizontalBar(w)
        self.egt.name = "Avg EGT"
        self.egt.units = "degF"
        self.egt.decimalPlaces = 0
        self.egt.lowRange = 0.0
        self.egt.highRange = 1500.0
        self.egt.resize(190, 75)
        self.egt.move(w.width() - 200, 620)
        self.egt.value = 1350

        if test == 'normal':
            self.flightData.pitchChanged.connect(a.setPitchAngle)
            self.flightData.rollChanged.connect(a.setRollAngle)
            self.flightData.headingChanged.connect(head_tape.setHeading)

        elif test == 'fgfs':
            self.timer = QTimer()
            #Timer Signal to run guiUpdate
            QObject.connect(self.timer,
                               SIGNAL("timeout()"), self.guiUpdate)
            # Start the timer 1 msec update
            self.timer.start(1)

            self.thread1 = fgfs.UDP_Process(self.queue)
            self.thread1.start()

        elif test == 'test':
            roll = QSlider(Qt.Horizontal, w)
            roll.setMinimum(-180)
            roll.setMaximum(180)
            roll.setValue(0)
            roll.resize(200, 20)
            roll.move(440, 100)

            pitch = QSlider(Qt.Vertical, w)
            pitch.setMinimum(-90)
            pitch.setMaximum(90)
            pitch.setValue(0)
            pitch.resize(20, 200)
            pitch.move(360, 180)

            smap = QSlider(Qt.Horizontal, w)
            smap.setMinimum(0)
            smap.setMaximum(30)
            smap.setValue(0)
            smap.resize(200, 20)
            smap.move(w.width() - 200, 200)

            srpm = QSlider(Qt.Horizontal, w)
            srpm.setMinimum(0)
            srpm.setMaximum(3000)
            srpm.setValue(0)
            srpm.resize(200, 20)
            srpm.move(w.width() - 200, 100)

            heading = QSpinBox(w)
            heading.move(0, instHeight + 100)
            heading.setRange(0, 360)
            heading.setValue(1)
            heading.hide
            heading.valueChanged.connect(head_tape.setHeading)

            #headingBug = QSpinBox(w)
            #headingBug.move(650, 680)
            #headingBug.setRange(0, 360)
            #headingBug.setValue(1)
            #headingBug.valueChanged.connect(h.setHeadingBug)

            alt_gauge = QSpinBox(w)
            alt_gauge.setMinimum(0)
            alt_gauge.setMaximum(10000)
            alt_gauge.setValue(0)
            alt_gauge.setSingleStep(10)
            alt_gauge.move(1100, 100)
            alt_gauge.valueChanged.connect(alt_tape.setAltimeter)

            as_gauge = QSpinBox(w)
            as_gauge.setMinimum(0)
            as_gauge.setMaximum(140)
            as_gauge.setValue(0)
            as_gauge.move(10, 100)
            as_gauge.valueChanged.connect(as_tape.setAirspeed)

            pitch.valueChanged.connect(a.setPitchAngle)
            roll.valueChanged.connect(a.setRollAngle)
            smap.valueChanged.connect(map.setValue)
            srpm.valueChanged.connect(rpm.setValue)

    def guiUpdate(self):
        """
        Pull messages from the Queue and updates the Respected gauges.
        """
        try:
            msg = self.queue.get(0)
            msg = msg.split(',')

            self.as_tape.setAirspeed(float(msg[0]))
            self.a.setPitchAngle(float(msg[1]))
            self.a.setRollAngle(float(msg[2]))
            self.head_tape.setHeading(float(msg[3]))
            self.alt_tape.setAltimeter(int(float(msg[4])))
            self.op.setValue(float(msg[9]))
            self.ot.setValue(float(msg[8]))
            self.egt.setValue(float(msg[10]))
            self.ff.setValue(float(msg[11]))
            self.rpm.setValue(int(float(msg[7])))
            self.fuel.setValue(float(msg[12]) + float(msg[13]))
        except Queue.Empty:
            pass

    def closeEvent(self, event):
        self.thread1.stop()
        self.thread1.join(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    parser = argparse.ArgumentParser(description='pyEfis')
    parser.add_argument('-m', '--mode', choices=['test', 'normal', 'fgfs'],
        default='normal', help='Run pyEFIS in specific mode')

    args = parser.parse_args()
    form = main(args.mode)
    form.show()

    if args.mode == 'normal':
        form.cfix.start()

    result = app.exec_()
    if args.mode == 'normal':
        form.cfix.quit()
    sys.exit(result)