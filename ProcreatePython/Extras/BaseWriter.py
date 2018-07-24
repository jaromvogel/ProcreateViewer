import struct
# from SiModel import SiDocument # still needs installing lzo

#
# Base class for all file exporter classes.
#
# This manages the file we are exporting to, stores a reference to the
# SiDocument being exported, and it contains utilities related to binary
# writing of data. This also allow us to abstract away endianity etc.
#
# We could set an endianness flag and then just let client code set which
# endianness the file should use and then handle the byte swapping transparently.
# Currently, all writing happens in little endian.
# For big endian, the struct.pack format strings would have to use ">" instead
# of "<", so a simple if-else in each putXXX() function should be enough.
#
# Not sure how to do "protected" members like in C++ in Python...
#
class BaseWriter:
    
    def __init__( self, document ):
        
        super.__init__( self )
            
        # The document must be an SiDocument instance
        # assert isinstance( document, SiDocument )
                
        self.fileName = ""
        self.document = document
                
        self.file = nil
        
        
    # To be overridden by derived classes. Call this to perform the export.
    def write( self, fileName ):
            
        self.fileName = fileName
        
    # internal
    def openFile( self ):
            
        self.file = open( self.fileName, "wb" )
                
                
    # internal
    def putUInt8( self, theInt ):
                
        # B = "unsigned char"
        self.file.write( struct.pack( "B", theInt ) )
            
            
    # internal
    def putUInt16( self, theInt ):
                
        # < = little endian, H = unsigned short
        self.file.write( struct.pack( "<H", theInt ) )


    # internal
    def putInt16( self, theInt ):
    
        # < = little endian, h = signed short
        self.file.write( struct.pack( "<h", theInt ) )
    
    
    # internal
    def putUInt32( self, theInt ):
            
        # < = little endian, I = unsigned int
        self.file.write( struct.pack( "<I", theInt ) )
    
    
    # internal
    def putInt32( self, theInt ):
        
        # < = little endian, i = signed int
        self.file.write( struct.pack( "<i", theInt ) )


    # internal
    def putFloat32( self, theFloat ):

        # < = little endian, f = float
        self.file.write( struct.pack( "<f" ), theFloat )
    
    
    # internal
    def putFloat64( self, theFloat ):
    
        # < = little endian, d = double
        self.file.write( struct.pack( "<d" ), theFloat )


    # internal
    def putPadding( self, numBytes ):
        
        if numBytes <= 0:
            return
        
        for i in range( 0, numBytes - 1 ):
            self.file.write( b"\x0" )