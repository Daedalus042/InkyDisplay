# Installation Notes
##### The installation was not flawless, in case the title wasn't obvious. This is a summation of all the steps I needed to do to get the inky library to install properly.

1. Clone the repository from https://github.com/pimoroni/inky.git
2. Enter the code and run the install script *install.sh*
3. The install script fails, but it does create the virtual environment for mucking around
4. In the install script, **numpy** is the first module to fail
- The log mentioned in the error output doesn't exist
- **numpy** complains **pkgconfig** is not found, installing it via **pip** causes 'found but error when run' error text
- Install **python3-dev** via apt, and install continues
5. Further in the install, **matplotlib** fails next
- **matplotlib** requires dependences **libxml2** and **libxslt**
- Install via apt **libxml2-dev** and **libxslt-dev**
6. Install should be able to run fully now

### Note that this requires compiling some components that took over an hour on the Pi zero, so I'd recommend initial install on a more powerful Pi

##### I may have missed something if bash crashed and ommitted the command history
