#
# TODO: Loads of sanity and error checks. And finishing everything, obviously.
#

# Standard includes
import shutil
import math
import os
import getpass

# Additional third-party packages
import biplist
import zipfile # comes with OS X
import lzo # argh!!!
import PIL

# This is where we currently extract the package to
# FIXME: This should likely go to $TMPDIR or /tmp. Also, if multiple instances
# of our code run in parallel, we are in deep trouble.
# Tried simply "~/procreate-temp/", but it doesn't seem to resolve the tilde
# FIXME: This path is specific to OS X!!!
G_TEMP_FILE_NAME = "/Users/" + getpass.getuser() + '/procreate-temp/'

#
# Rectangle
#
class SiRect:
    
    def __init__( self ):
        
        self.top = ( 0, 0 )
        self.bottom = ( 0, 0 )

#
# RGB Color
#
class SiColor:

    def __init__( self, r, g, b, a ):

        self.r = r
        self.g = g
        self.b = b
        self.a = a

#
# Layer in an SiDocument.
#
class SiLayer:
    
    # Layer blend modes
    BLEND_MODE_NORMAL = 0
    # TODO: ...
    
    def __init__( self, document ):
        
        # Document we belong to
        self.document = document
        
        # Set all values to default
        self.clear()
    
    
    def clear( self ):
    
        # Layer name
        self.name = ""
        
        # Layer bounds
        self.contentsRect = SiRect()
        self.contentsRectValid = False
        
        # Various attributes
        self.uuid = "000000000000-0000-0000-000000000000"
        self.name = ""
        self.blend = 0
        self.opacity = 1
        self.hidden = False
        self.locked = False
        self.perspectiveAssisted = False
        self.preserve = False
        self.type = 1 # default from test file
        self.version = 2 # default from test file
        
        # PIL RGBA Image buffer containing the raster data
        self.imageBuffer = None


    def dump( self ):
    
        print( "SiLayer" )
        print( "\tuuid: " + self.uuid )
        print( "\tname: " + self.name )
        print( "\tblend: " + str( self.blend ) + " (" + self.blendModeToString( self.blend ) + ")" )
        print( "\topacity: " + str( self.opacity ) )
        print( "\thidden: " + str( self.hidden ) )
        print( "\tlocked: " + str( self.locked ) )
        print( "\tperspectiveAssisted: " + str( self.perspectiveAssisted ) )
        print( "\tpreserve: " + str( self.preserve ) )
        print( "\ttype: " + str( self.type ) )
        print( "\tversion: " + str( self.version ) )
        print( "\ttransform: <todo>" )
        #...
    
    
    # Given a layer object in a PList, and the PList object array, this
    # reads the data about the layer.
    # INTERNAL. Called by SiDocument's reading routines.
    def readFromPlistObj( self, layerPlistObj, plistObjs, loadImageData = True ):
        
        # We depend on the document for tile and canvas size etc.
        assert self.document != None
        
        # The UUID property is the index of the string object that stores the
        # actual UUID value
        uuidIdx = layerPlistObj.get( 'UUID' ).integer
        # Read precisely that object
        self.uuid = plistObjs[ uuidIdx ]
        
        # Same thing for the name, which is an object index to a string
        nameIdx = layerPlistObj.get( 'name' ).integer
        self.name = plistObjs[ nameIdx ]
        
        self.blend = layerPlistObj.get( 'blend ' )
        self.opacity = layerPlistObj.get( 'opacity' )
        self.hidden = layerPlistObj.get( 'hidden' )
        self.locked = layerPlistObj.get( 'locked' )
        self.perspectiveAssisted = layerPlistObj.get( 'perspectiveAssisted' )
        self.preserve = layerPlistObj.get( 'preserve' )
        self.type = layerPlistObj.get( 'type' )
        self.version = layerPlistObj.get( 'version' )

        # TODO: Read transform. Sounds kind of relevant :)
        
        if loadImageData == False:
            return
        
        # We can now get a list of all chunk files
        layerBasePath = G_TEMP_FILE_NAME + "/" + self.uuid + "/"
        chunkfileList = os.listdir( layerBasePath )
        
        # Allocate an image buffer for the entire layer
        assert self.document.width  > 0
        assert self.document.height > 0
        self.imageBuffer = PIL.Image.new (
            'RGBA',
            ( self.document.width, self.document.height )
        )
        
        for fileName in chunkfileList:
            
            # ----- decode tile -----
            
            columnIdx = int( fileName.strip( '.chunk' ).split( '~' )[ 0 ] )
            rowIdx    = int( fileName.strip( '.chunk' ).split( '~' )[ 1 ] )
            
            tileSizeX = self.document.tileSize
            tileSizeY = self.document.tileSize

            # Edge tiles may be smaller than the standard tile size so we need
            # to compensate for the size difference
            if columnIdx == self.document.numTileColumns - 1:
                tileSizeX = self.document.width  % self.document.tileSize
            if rowIdx == self.document.numTileRows - 1:
                tileSizeY = self.document.height % self.document.tileSize
            
            # Read the entire chunk into a memory buffer
            chunkFile = open( layerBasePath + fileName, "rb" )
            srcData = chunkFile.read()
            
            # No need to keep the file object around and open.
            # My C++ habits getting the better of me I guess.
            chunkFile = None

            # LZO decompress
            outputSize = tileSizeX * tileSizeY * 4
            outData = lzo.decompress( srcData, False, outputSize )

            # Create a PIL image from the tile
            tileImage = PIL.Image.frombytes (
                'RGBA',
                ( tileSizeX, tileSizeY ),
                outData
            )
            
            # Reverse row order (tiles are stored flipped vertically)
            tileImage = tileImage.transpose( PIL.Image.FLIP_TOP_BOTTOM )

            # ----- draw tile into layer buffer -----

            # Compute the raster position of the tile inside the image
            rasterPosX = columnIdx * self.document.tileSize
            rasterPosY = self.document.height - rowIdx * self.document.tileSize

            # If we're at the last row (topmost), we need to deal with the
            # non-full-size tile
            if rowIdx == self.document.numTileRows:
                rasterPosY = 0

            # Blit the tile into our image buffer
            self.imageBuffer.paste( tileImage, ( rasterPosX, rasterPosY ) )

            # If the image is stored rotated, undo that rotation
            # FIXME: Wouldn't that imply document width and height might be inaccurate?
            if self.document.orientation == 3:
                canvas = canvas.rotate(  90, expand = True )
            elif self.document.orientation == 4:
                canvas = canvas.rotate( -90, expand = True )
            elif self.document.orientation == 2:
                canvas = canvas.rotate( 180, expand = True )

            # Deal with flipped images
            if self.document.flippedHorizontally == 1 and ( self.document.orientation == 1 or self.document.orientation == 2 ):
                self.imageBuffer = self.imageBuffer.transpose( PIL.Image.FLIP_LEFT_RIGHT )
            if self.document.flippedHorizontally == 1 and ( self.document.orientation == 3 or self.document.orientation == 4):
                self.imageBuffer = self.imageBuffer.transpose( PIL.Image.FLIP_TOP_BOTTOM )
            if self.document.flippedVertically == 1 and ( self.document.orientation == 1 or self.document.orientation == 2):
                self.imageBuffer = self.imageBuffer.transpose( PIL.Image.FLIP_TOP_BOTTOM )
            if self.document.flippedVertically == 1 and ( self.document.orientation == 3 or self.document.orientation == 4):
                self.imageBuffer = self.imageBuffer.transpose( PIL.Image.FLIP_LEFT_RIGHT )


    # Returns a string identifying the blend mode of the layer.
    # Useful for debugging and for outputting to text-based formats.
    def blendModeToString( self ):

        blendModeStrings = {
            BLEND_MODE_NORMAL   : "Normal",
            BLEND_MODE_MULTIPLY : "Multiply"
            # ...
        }
        
        if self.blend in blendModeStrings:
            return blendModeStrings[ self.blend ]
        else:
            return "Normal"



#
# Represents a Procreate Document.
#
# Example:
#
#   doc = SiDocument( "myFile.procreate" )
#   print( "The number of layers is: " + str( len( doc.layers ) ) )
#   print( "The tracked time is " + str( doc.trackedTime ) )
#
class SiDocument:
    
    def __init__( self ):
        
        self.clear()
    
    # FIXME: Apparently, Python does not support overloaded constructors!!!!
    def __init__( self, fileName ):
        
        self.clear()
        self.loadFile( fileName )
    
    # Initialize to an empty 0x0 document.
    # You can use the code as a reference for properties of this class.
    def clear( self ):
        
        self.width  = 0
        self.height = 0
        self.trackedTime = 0.0
        self.orientation = 0 # TODO: What are the valid values?
        self.tileSize = 256
        self.numTileColumns = 0 # computed, not read
        self.numTileRows = 0 # computed, not read
        self.flippedHorizontally = False
        self.flippedVertically = False
        self.dpi = 132 # Default taken from a sample file
        self.videoPurged = False
        self.backgroundHidden = False
        
        self.composite = None # of type SiLayer when present
        self.mask = None # also of type SiLayer when present
        
        # Array of objects of type SiLayer
        self.layers = []
    
    
    # Print our member variables to the console for debugging
    def dump( self ):
    
        print( "SiDocument:" )
        print( "\tversion: " + str( self.version ) )
        print( "\twidth: " + str( self.width ) )
        print( "\theight: " + str( self.height ) )
        print( "\ttrackedTime: " + str( self.trackedTime ) )
        print( "\torientation: " + str( self.orientation ) )
        print( "\ttileSize: " + str( self.tileSize ) )
        print( "\tnumTileRows: " + str( self.numTileRows ) )
        print( "\tnumTileColumns: " + str( self.numTileColumns ) )
        print( "\tflippedHorizontally: " + str( self.flippedHorizontally ) )
        print( "\tflippedVertically: " + str( self.flippedVertically ) )
        print( "\tdpi: " + str( self.dpi ) )
        print( "\tvideoPurged: " + str( self.videoPurged ) )
        print( "\tbackgroundHidden: " + str( self.backgroundHidden ) )
        
        if self.composite == None:
            print( "\tcomposite: None" )
        else:
            print( "\tcomposite:" )
            self.composite.dump()


    # INTERNAL. This handles opening of the file. Separate from loadFile() since
    # it can be re-used for things like extracting the QuickLook thumbnail
    # or the time-lapse video if present.
    def openFile( self, fileName ):
    
        # Extract the main ZIP file.
        # FIXME: It might be cleaner to create a pipe to unzip and thus have
        # files unzipped to memory
        zipFile = zipfile.ZipFile( fileName, 'r' )
        zipFile.extractall( G_TEMP_FILE_NAME )
    
    
    # INTERNAL: Deletes the temporary folder where we extracted the ZIP file
    def closeFile( self ):
    
        # Delete our temporary file
        shutil.rmtree( G_TEMP_FILE_NAME )
    
    
    # TODO. Also, DO NOT CALL THIS DURING loadFile() or we'll prematurely
    # delete our temp directory.
    def extractQuickLookThumbnail( self, fileName, outputFile ):
    
        self.openFile( fileName )
        
        # TODO
        
        self.closeFile()


    # ...
    def extractTimelapseVideo( self, fileName ):
    
        pass
    

    # Load a Procreate file with the given file name from disk. Set readLayers
    # to False to only read the composite. By default, both composite and layer
    # data are read.
    def loadFile( self, fileName, readLayers = False ):
        
        # Get rid of any previous data in this document
        self.clear()
        
        # Unzip the .procreate file
        self.openFile( fileName )
        
        # Read the "Document.archive" PList file
        plist = biplist.readPlist( G_TEMP_FILE_NAME + 'Document.archive' )
        objects = plist.get('$objects')
        docObj = objects[ 1 ]
        
        # Version
        self.version = docObj.get( 'version' )
        
        # Work out index of the NSString object that encodes the size
        sizeIdx = docObj.get( 'size' ).integer
        # Fetch that string object
        sizeStrObj = objects[ sizeIdx ]
        # Decode the string contained in there into a tuple of two values
        sizes = sizeStrObj.strip('{').strip('}').split(', ')
        # Set the member value
        self.width  = int( sizes[ 0 ] )
        self.height = int( sizes[ 1 ] )
        
        self.tileSize = docObj.get( 'tileSize' )
        self.orientation = docObj.get( 'orientation' )
        
        # Compute how many tiles there are in each direction
        self.numTileColumns = int( math.ceil( float( self.width  ) / float( self.tileSize ) ) )
        self.numTileRows    = int( math.ceil( float( self.height ) / float( self.tileSize ) ) )
        
        # Get all sorts of other attributes (could go into XMP metadata)
        self.trackedTime = docObj.get( 'SilicaDocumentTrackedTimeKey' )
        self.dpi = docObj.get( 'SilicaDocumentArchiveDPIKey' )
        self.videoPurged = docObj.get( 'SilicaDocumentVideoPurgedKey' )
        self.backgroundHidden = docObj.get( 'backgroundHidden' )
        
        # Background color is a separate object
        bgColorIdx = docObj.get( 'backgroundColor' ).integer
        bgColorData = objects[ bgColorIdx ] #NSData apparently
        #print( "bg color string is " + str( bgColorData ) )
        
        # Composite is a separate SiLayer with flattened image data
        compositeObjIdx = docObj.get( 'composite' ).integer
        self.composite = SiLayer()
        self.composite.readFromPlistObj( objects[ compositeObjIdx ], objects )
        
        if readLayers == True:
            # Figure out the index of the NSArray with the layers in the
            # PList's object list
            layersIdx = docObj.get( 'layers' ).integer
        
            # TODO: Decode tha NSArray somehow
            # layerPlistObj = ...
            
            #layer = SiLayer( self )
            #layer.readFromPlistObj( layerPlistObj, objects )
            #self.layers.append( layer )
        
        # Delete our temporary file
        self.closeFile()


#
# Single swatch in an SiPalette
#
class SiSwatch:
    
    pass

#
# Procreate color palette file
#
class SiPalette:
    
    pass

#
# Procreate brush parameters
#
class SiBrush:
    
    pass