from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class JELLYPOX( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py', cargs=('log --file=pox/ext/jelly.log,w openflow.of_01 --port=%s ext.jelly_controller2' ),
                  **kwargs ):
        print "gonna init the controller"
        print str(Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs ))
controllers={ 'jelly': JELLYPOX }
