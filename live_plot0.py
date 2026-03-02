import sys
import random
import math
import time
import threading
from collections import deque
import serial
from PyQt5 import QtWidgets
import pyqtgraph as pg


# ============================================================
# Dummy Data Generator (used instead of COM port)
# ============================================================
class DummySerial:
    """Generates sine and cosine CSV data, e.g.: 0.707,-0.707"""

    def __init__(self, period=0.02, freq=0.20, noise=0.12):
        self.period = period     # time between samples
        self.freq = freq         # sine wave frequency
        self.noise = noise       # random noise amplitude
        self._running = True
        self._t = 0.0            # internal time counter

    def readline(self):
        """Generate sine + cosine data as CSV string."""
        if not self._running:
            return b""

        # Calculate sine and cosine
        sin_val = math.sin(2 * math.pi * self.freq * self._t)
        cos_val = math.cos(2 * math.pi * self.freq * self._t)

        # Add a bit of random noise (optional)
        sin_val += random.uniform(-self.noise, self.noise)
        cos_val += random.uniform(-self.noise, self.noise)

        # Increase time
        self._t += self.period

        time.sleep(self.period)

        return f"{sin_val:.4f},{cos_val:.4f}\n".encode()

    def close(self):
        self._running = False


# ============================================================
# Background thread for reading from serial
# ============================================================
class SerialReader(threading.Thread):
    def __init__(self, serial_port, callback):
        super().__init__()
        self.ser = serial_port
        self.callback = callback
        self.daemon = True
        self.start()

    def run(self):
        while True:
            line = self.ser.readline().decode().strip()
            if not line:
                continue
            try:
                values = list(map(float, line.split(",")))
                self.callback(values)
            except:
                # ignore malformed lines
                continue


# ============================================================
# PyQtGraph Live Plot Window
# ============================================================
class LivePlot(QtWidgets.QMainWindow):
    def __init__(self, use_dummy=True, com_port="COM5", baud=115200):
        super().__init__()

        self.setWindowTitle("Live CSV Data Plotter")
        self.resize(900, 500)

        # Graph widget
        self.plot_widget = pg.PlotWidget(title="Live Data")
        self.setCentralWidget(self.plot_widget)

        # Two curves (two data columns)
        self.curve_a = self.plot_widget.plot(pen="y", name="Channel A")
        self.curve_b = self.plot_widget.plot(pen="c", name="Channel B")

        # Data buffers
        self.buffer_size = 500
        self.data_a = deque([0] * self.buffer_size, maxlen=self.buffer_size)
        self.data_b = deque([0] * self.buffer_size, maxlen=self.buffer_size)

        # Set up serial (real or dummy)
        if use_dummy:
            self.serial = DummySerial()
        else:
            self.serial = serial.Serial(com_port, baud, timeout=1)

        # Background read thread
        self.reader = SerialReader(self.serial, self.on_data)

        # Update timer
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_graph)
        self.timer.start(20)

        # ============================================================
        # Vertical Marker Line
        # ============================================================
        self.marker = pg.InfiniteLine(pos=0, angle=90, movable=True, pen=pg.mkPen('m', width=2))
        self.plot_widget.addItem(self.marker)

        # When marker moves, update value display
        self.marker.sigPositionChanged.connect(self.update_marker_values)

        # Text legend (won't be flipped)
        self.legend_text = pg.TextItem(
            text="",
            anchor=(0, 0),
            color="w"
        )
        self.plot_widget.getViewBox().addItem(self.legend_text, ignoreBounds=True)


    def update_marker_values(self):
        x = self.marker.value()
        idx = int(x)

        if 0 <= idx < len(self.data_a):
            a_val = self.data_a[idx]
            b_val = self.data_b[idx]

            self.legend_text.setText(
                f"Index: {idx}\n"
                f"sin: {a_val:.4f}\n"
                f"cos: {b_val:.4f}"
            )
        else:
            self.legend_text.setText("Out of range")


    def on_data(self, values):
        """Gets called for every CSV line."""
        if len(values) >= 2:
            self.data_a.append(values[0])
            self.data_b.append(values[1])

    def update_graph(self):
        self.curve_a.setData(list(self.data_a))
        self.curve_b.setData(list(self.data_b))

        # Keep the marker inside valid range
        max_x = len(self.data_a) - 1
        if self.marker.value() > max_x:
            self.marker.setValue(max_x)

        self.update_legend_position()

        self.update_marker_values()

    def update_legend_position(self):
        vb = self.plot_widget.getViewBox()

        # Convert from scene pixel coords → data coords
        # 10 px from left, 10 px from top
        pos = vb.mapSceneToView(pg.QtCore.QPointF(50, 70))

        self.legend_text.setPos(pos.x(), pos.y())

# ============================================================
# MAIN
# ============================================================
def main():
    app = QtWidgets.QApplication(sys.argv)

    # Change use_dummy=False to read from real COM port
    window = LivePlot(use_dummy=True)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
