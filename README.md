# runFinder-python+flask+javascript

Source code for [runFindr.net](http://www.runfindr.net/) an Insight Data Science project by Joerg Fritz

## Status

This is a work in progress.

## Dependencies

* Python 2.7
  * [Flask](http://flask.pocoo.org/) the frame work the website is built on.
  * [MySQLdb](http://mysql-python.sourceforge.net/MySQLdb.html) so we can talk to mySQL databases.
  * [gpxpy](https://github.com/tkrajina/gpxpy) for export of routes to gpx files.
  * [scipy.stats](http://docs.scipy.org/doc/scipy-0.13.0/reference/stats.html) for statistics
  * [numpy](http://www.numpy.org/) for faster scientific computing.
  * [Haversine](https://pypi.python.org/pypi/haversine) because we want to calculate distances properly.

## Usage

The main flask code is in flask_app.py. The code references databases that can be reproduced with code
in [genRouteDb](https://github.com/JoergFritz/genRouteDb), which can also be found on github.