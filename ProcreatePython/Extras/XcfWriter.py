
from SiModel import *
from BaseWriter import BaseWriter

#
# Enum values for XCF properties.
# Internal use only.
#
class XcfProperty():

    PROP_END                =  0,
    PROP_COLORMAP           =  1,
    PROP_ACTIVE_LAYER       =  2,
    PROP_ACTIVE_CHANNEL     =  3,
    PROP_SELECTION          =  4,
    PROP_FLOATING_SELECTION =  5,
    PROP_OPACITY            =  6,
    PROP_MODE               =  7,
    PROP_VISIBLE            =  8,
    PROP_LINKED             =  9,
    PROP_LOCK_ALPHA         = 10,
    PROP_APPLY_MASK         = 11,
    PROP_EDIT_MASK          = 12,
    PROP_SHOW_MASK          = 13,
    PROP_SHOW_MASKED        = 14,
    PROP_OFFSET             = 15,
    PROP_COLOR              = 16,
    PROP_COMPRESSION        = 17,
    PROP_GUIDES             = 18,
    PROP_RESOLUTION         = 19,
    PROP_TATTOO             = 20,
    PROP_PARASITES          = 21,
    PROP_UNIT               = 22,
    PROP_PATHS              = 23,
    PROP_USER_UNIT          = 24,
    PROP_VECTORS            = 25,
    PROP_TEXT_LAYER_FLAGS   = 26,
    PROP_SAMPLE_POINTS      = 27, # The spec doc says 17, but it lies.
    PROP_LOCK_CONTENT       = 28,
    PROP_GROUP_ITEM         = 29,
    PROP_ITEM_PATH          = 30,
    PROP_GROUP_ITEM_FLAGS   = 31,
    PROP_LOCK_POSITION      = 32


#
# Export an SiDocument to Gimp XCF file.
#
# Usage is identical to PsdWriter.
#
# Slightly outdated specification: http://henning.makholm.net/xcftools/xcfspec-saved
#
class XcfWriter( BaseWriter ):
    
    
    def __init__( self, document ):
        
        super.__init__( self, document )
    
    
    # Call this to write the document to a layered XCF file with the
    # given file name.
    def write( self, fileName ):
        
        super.write( fileName )
        
        self.openFile()
        
        self.writeXcf()
    

    # Handle the output to XCF
    def writeXcf( self ):
        
        self.writeHeader()
        self.writePropertyList()
        self.writeLayers()
        self.writeChannels()
    
    
    # INTERNAL
    def writeHeader( self ):
        
        # Note the trailing space, it's important.
        self.file.write( b"gimp xcf " )

        # File version (latest)
        self.file.write( b"v003" )

        # Unused (null-terminator for version string)
        self.putUInt8( 0 )

        # Canvas width in pixels
        self.putUint32( self.document.width )

        # Canvas height in pixels
        self.putUint32( self.document.height )

        # Base Type (color mode, we use 0 for RGB)
        self.putUint32( 0 )


    # INTERNAL
    def writePropertyList( self ):
       
        # This is marked as essential in the spec. Data compression used.
        self.writePropCompression()
    
        # This specifies the resolution (DPI) of the image
        self.writePropResolution()
    
        # Special property that marks the end of the properties list
        self.writePropEnd()


    # INTERNAL
    def writePropCompression( self ):
    
        # Property Type
        self.putUint32( XcfProperty.PROP_COMPRESSION )
    
        # Payload is one byte
        self.putUint32( 1 )
    
        # Compression. 0 = None, 1 = RLE (default). Other values are defined,
        # but not used/supported.
        # For now, we store data uncompressed.
        self.putUInt8( 0 )
    
    
    # INTERNAL
    def writePropResolution( self ):
        
        # Property Type
        self.putUint32( XcfProperty.PROP_RESOLUTION )
    
        # Payload is 8 bytes in length
        self.putUint32( 8 )
        
        # Resolution in each X and Y
        self.putFloat32( self.document.dpi )
        self.putFloat32( self.document.dpi )
    

    # INTERNAL
    def writePropEnd( self ):
    
        # Property Type
        self.putUint32( XcfProperty.PROP_END )
    
        # Payload length (there is no payload)
        self.putUint32( 0 )
    

    # INTERNAL
    def writeLayers( self ):

        for layer in self.document.layers:
            
            # TODO: Write offset of the beginning of the corresponding layer
            # structure. XCF files just require that the header and property
            # list (which is sort of part of the header apparently) come first,
            # then the layer pointers (offset table), then the channel pointers,
            # and then it's basically free.
            # Since the layer structure contains a variable-length string and a
            # property list, this looks kind of like a nuissance to me frankly.
            pass
        
        # Layer list end marker
        self.putUint32( 0 )


    # INTERNAL
    def writeChannels( self ):

        # TODO

        # Channel list end marker
        self.putUint32( 0 )