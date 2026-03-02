Visualizing live data

This script gives an idea how to get the things working
By default, dumy serial port is used as data generator.

To use real serial port change
    window = LivePlot(use_dummy=True)
to (example)
    window = LivePlot(use_dummy=False, com_port="COM5", baud=115200)

here
# ============================================================
# MAIN
# ============================================================
def main():
    app = QtWidgets.QApplication(sys.argv)

    # Change use_dummy=False to read from real COM port
    window = LivePlot(use_dummy=True)
    window.show()

    sys.exit(app.exec_())